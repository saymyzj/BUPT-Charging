import sqlite3
from pathlib import Path
from flask import current_app, g, has_app_context


_standalone_database_path = None


def _resolve_migrations_dir(database_path: str) -> Path:
    migrations_dir = Path(database_path).resolve().parent / 'migrations'
    if not migrations_dir.exists():
        migrations_dir = Path(__file__).resolve().parents[2] / 'migrations'
    return migrations_dir


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
            db = get_db()
            migrations_dir = _resolve_migrations_dir(current_app.config['DATABASE_PATH'])
            schema_path = migrations_dir / 'init_schema_v2.sql'
            if not schema_path.exists():
                schema_path = migrations_dir / 'init_schema.sql'

            with open(schema_path, 'r', encoding='utf-8') as f:
                db.executescript(f.read())
            db.commit()
            close_db()

        app.teardown_appcontext(close_db)
        return

    database_path = str(app_or_path)
    global _standalone_database_path
    _standalone_database_path = database_path
    migrations_dir = _resolve_migrations_dir(database_path)
    schema_path = migrations_dir / 'init_schema_v2.sql'
    if not schema_path.exists():
        schema_path = migrations_dir / 'init_schema.sql'

    db = sqlite3.connect(database_path)
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        db.commit()
    finally:
        db.close()


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
