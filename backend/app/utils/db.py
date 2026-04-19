import sqlite3
from datetime import datetime
from pathlib import Path
from flask import current_app, g, has_app_context


_standalone_database_path = None
SQLITE_REBUILD_ERROR_MARKERS = (
    'disk i/o error',
    'database disk image is malformed',
    'file is not a database',
    'readonly database',
    'unable to open database file',
)
V3_REQUIRED_COLUMNS = {
    'user': {'user_id', 'username', 'password_hash', 'battery_capacity', 'role'},
    'charging_station': {
        'station_code',
        'charge_mode',
        'power_kw',
        'station_status',
        'queue_capacity',
        'current_queue_length',
    },
    'charge_request': {
        'request_id',
        'user_id',
        'charge_mode',
        'request_energy',
        'request_status',
        'queue_number',
        'waiting_area_order',
        'station_id',
        'station_queue_position',
        'request_time',
    },
    'request_detail': {
        'detail_id',
        'request_id',
        'user_id',
        'station_code',
        'actual_energy',
        'charge_fee',
        'service_fee',
        'total_fee',
        'request_status',
    },
    'scheduler_config': {'config_key', 'config_value'},
}


def _resolve_migrations_dir(database_path: str) -> Path:
    migrations_dir = Path(database_path).resolve().parent / 'migrations'
    if not migrations_dir.exists():
        migrations_dir = Path(__file__).resolve().parents[2] / 'migrations'
    return migrations_dir


def _schema_path(database_path: str) -> Path:
    migrations_dir = _resolve_migrations_dir(database_path)
    schema_path = migrations_dir / 'init_schema_v3.sql'
    if not schema_path.exists():
        schema_path = migrations_dir / 'init_schema_v2.sql'
    if not schema_path.exists():
        schema_path = migrations_dir / 'init_schema.sql'
    return schema_path


def _table_names(db):
    return {
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }


def _table_columns(db, table_name: str):
    return {row[1] for row in db.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _schema_is_v3_compatible(db) -> bool:
    tables = _table_names(db)
    if not tables:
        return True
    for table_name, required_columns in V3_REQUIRED_COLUMNS.items():
        if table_name not in tables:
            return False
        if not required_columns.issubset(_table_columns(db, table_name)):
            return False
    return True


def _auto_rebuild_incompatible_db() -> bool:
    if not has_app_context():
        return True
    return str(current_app.config.get('AUTO_REBUILD_INCOMPATIBLE_DB', True)).lower() not in {
        '0',
        'false',
        'no',
    }


def _backup_incompatible_database(database_path: str) -> Path:
    source = Path(database_path)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup = source.with_name(f"{source.name}.legacy-{timestamp}.bak")
    counter = 1
    while backup.exists():
        backup = source.with_name(f"{source.name}.legacy-{timestamp}-{counter}.bak")
        counter += 1
    source.rename(backup)
    return backup


def _cleanup_sqlite_sidecars(database_path: str):
    source = Path(database_path)
    for suffix in ('-journal', '-wal', '-shm'):
        sidecar = Path(f'{source}{suffix}')
        if sidecar.exists():
            sidecar.unlink()


def _should_rebuild_for_sqlite_error(exc: sqlite3.Error) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in SQLITE_REBUILD_ERROR_MARKERS)


def _create_fresh_database(database_path: str, schema_path: Path, apply_runtime_config: bool = False):
    db = sqlite3.connect(database_path)
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        if apply_runtime_config:
            _apply_runtime_config(db)
        db.commit()
    finally:
        db.close()


def _rebuild_database_file(
    database_path: str,
    schema_path: Path,
    apply_runtime_config: bool = False,
    reason: str | None = None,
):
    backup_path = None
    if Path(database_path).exists():
        backup_path = _backup_incompatible_database(database_path)
    _cleanup_sqlite_sidecars(database_path)
    _create_fresh_database(database_path, schema_path, apply_runtime_config)
    if has_app_context():
        if backup_path:
            current_app.logger.warning(
                "SQLite database was rebuilt from %s because %s; backup saved to %s.",
                database_path,
                reason or 'it was incompatible with V3',
                backup_path,
            )
        else:
            current_app.logger.warning(
                "SQLite database was initialized at %s because %s.",
                database_path,
                reason or 'no compatible database was available',
            )
    return backup_path


def _initialize_database_file(database_path: str, apply_runtime_config: bool = False):
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = _schema_path(database_path)
    auto_rebuild = _auto_rebuild_incompatible_db()

    try:
        db = sqlite3.connect(database_path)
        try:
            if not _schema_is_v3_compatible(db):
                raise RuntimeError(
                    "Database schema is incompatible with V3. Set DB_PATH to a fresh V3 database "
                    "or migrate/backup the existing SQLite file before starting."
                )
            with open(schema_path, 'r', encoding='utf-8') as f:
                db.executescript(f.read())
            if apply_runtime_config:
                _apply_runtime_config(db)
            db.commit()
            return
        finally:
            db.close()
    except RuntimeError:
        if not auto_rebuild:
            raise
        _rebuild_database_file(
            database_path,
            schema_path,
            apply_runtime_config,
            reason='the existing schema was incompatible with V3',
        )
    except sqlite3.Error as exc:
        if not auto_rebuild or not Path(database_path).exists() or not _should_rebuild_for_sqlite_error(exc):
            raise
        _rebuild_database_file(
            database_path,
            schema_path,
            apply_runtime_config,
            reason=f'sqlite reported "{exc}"',
        )


def _apply_runtime_config(db):
    if not has_app_context():
        return

    request_count = db.execute("SELECT COUNT(*) FROM charge_request").fetchone()[0]
    if request_count == 0:
        db.execute("DELETE FROM charging_station")
        queue_len = int(current_app.config.get('CHARGING_QUEUE_LEN', 2))
        for index in range(1, int(current_app.config.get('FAST_CHARGING_PILE_NUM', 3)) + 1):
            db.execute(
                """
                INSERT INTO charging_station (station_code, charge_mode, power_kw, station_status, queue_capacity)
                VALUES (?, 'FAST', 30.0, 'RUNNING', ?)
                """,
                (f"FAST_{index:02d}", queue_len),
            )
        for index in range(1, int(current_app.config.get('TRICKLE_CHARGING_PILE_NUM', 2)) + 1):
            db.execute(
                """
                INSERT INTO charging_station (station_code, charge_mode, power_kw, station_status, queue_capacity)
                VALUES (?, 'SLOW', 10.0, 'RUNNING', ?)
                """,
                (f"SLOW_{index:02d}", queue_len),
            )

    config_values = {
        'fast_station_count': int(current_app.config.get('FAST_CHARGING_PILE_NUM', 3)),
        'slow_station_count': int(current_app.config.get('TRICKLE_CHARGING_PILE_NUM', 2)),
        'waiting_area_capacity': int(current_app.config.get('WAITING_AREA_SIZE', 6)),
        'charging_queue_len': int(current_app.config.get('CHARGING_QUEUE_LEN', 2)),
        'dispatch_mode': current_app.config.get('DISPATCH_MODE', 'NORMAL'),
        'fault_dispatch_mode': current_app.config.get('FAULT_DISPATCH_MODE', 'TIME_ORDER'),
    }
    for key, value in config_values.items():
        db.execute(
            """
            INSERT INTO scheduler_config (config_key, config_value)
            VALUES (?, ?)
            ON CONFLICT(config_key) DO UPDATE SET config_value = excluded.config_value
            """,
            (key, value),
        )


def get_db():
    """
    获取数据库连接
    使用Flask的g对象存储连接，确保同一请求内复用
    """
    if has_app_context():
        if 'db' not in g:
            g.db = sqlite3.connect(current_app.config['DATABASE_PATH'])
            g.db.row_factory = sqlite3.Row
        return g.db

    if not _standalone_database_path:
        raise RuntimeError("Database is not initialized for standalone access")

    db = sqlite3.connect(_standalone_database_path)
    db.row_factory = sqlite3.Row
    return db


def close_db(e=None):
    """
    关闭数据库连接
    在请求结束时自动调用
    """
    if has_app_context():
        db = g.pop('db', None)
        if db is not None:
            db.close()


def init_db(app_or_path):
    """
    初始化数据库
    创建所有表和初始数据
    """
    if hasattr(app_or_path, 'app_context'):
        app = app_or_path
        with app.app_context():
            _initialize_database_file(current_app.config['DATABASE_PATH'], apply_runtime_config=True)

        app.teardown_appcontext(close_db)
        return

    database_path = str(app_or_path)
    global _standalone_database_path
    _standalone_database_path = database_path
    _initialize_database_file(database_path)


def query_db(query, args=(), one=False):
    """
    执行查询语句
    
    Args:
        query: SQL查询语句
        args: 查询参数
        one: 是否只返回一条记录
    
    Returns:
        查询结果（字典或字典列表）
    """
    db = get_db()
    try:
        cur = db.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        if one:
            return rv[0] if rv else None
        return rv
    finally:
        if not has_app_context():
            db.close()


def execute_db(query, args=()):
    """
    执行更新语句（INSERT/UPDATE/DELETE）
    
    Args:
        query: SQL语句
        args: 语句参数
    
    Returns:
        最后插入行的ID
    """
    db = get_db()
    try:
        cur = db.execute(query, args)
        db.commit()
        return cur.lastrowid
    finally:
        if not has_app_context():
            db.close()
