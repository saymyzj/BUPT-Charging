"""
调度引擎模块

成员A负责提供的最小可用调度能力：
1. 单请求预测
2. 关键事件后的统一重调度
3. 批量模拟执行内核
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.enums import ChargeMode, EventType, RequestStatus, StationStatus, WaitingPoolType
from app.utils.db import execute_db, query_db


FAST_POWER_KW = 30.0
SLOW_POWER_KW = 7.0
DEFAULT_CALL_AHEAD_SECONDS = 300
DEFAULT_CONFIRM_TIMEOUT_SECONDS = 180
DEFAULT_LEAVE_DELAY_SECONDS = 120
DEFAULT_VIRTUAL_REQUEST_ENERGY = 20.0
ENERGY_PRICE = 1.5


@dataclass
class RuntimeStation:
    """调度过程中使用的充电桩运行态。"""

    station_id: Optional[int]
    station_code: str
    station_type: str
    power_kw: float
    available_at: datetime
    status: str
    busy_seconds: int = 0


@dataclass
class RuntimePrediction:
    """调度预测结果。保持路由层依赖的核心字段稳定。"""

    id: int
    request_id: str
    queue_position: int
    estimated_wait_seconds: Optional[int]
    estimated_start_time: Optional[datetime]
    estimated_finish_time: Optional[datetime]
    estimated_service_seconds: int
    recommended_station_id: Optional[int]
    recommended_station_code: Optional[str]
    priority_score: float


def parse_datetime(value: Any, fallback: Optional[datetime] = None) -> datetime:
    """兼容 ISO 8601 和 SQLite datetime 文本。"""
    if isinstance(value, datetime):
        return value
    if value is None:
        if fallback is not None:
            return fallback
        return datetime.now()
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass
    if fallback is not None:
        return fallback
    return datetime.now()


def format_datetime(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.strftime("%Y-%m-%dT%H:%M:%S")


def service_seconds_for_request(request_energy: float, charge_mode: str, power_kw: Optional[float] = None) -> int:
    """按文档中的功率约定计算预计服务时长。"""
    if power_kw is None:
        power_kw = FAST_POWER_KW if charge_mode == ChargeMode.FAST.value else SLOW_POWER_KW
    if power_kw <= 0:
        return 0
    return max(0, int(round(float(request_energy) / float(power_kw) * 3600)))


def _get_scheduler_numeric_config(config_key: str, default_value: float) -> float:
    row = query_db(
        "SELECT config_value FROM scheduler_config WHERE config_key = ?",
        [config_key],
        one=True,
    )
    if not row:
        return default_value
    try:
        return float(row["config_value"])
    except (TypeError, ValueError):
        return default_value


def _load_priority_weights() -> Dict[str, float]:
    """
    加载调度权重。

    文档冻结的是输入输出和语义，不冻结具体公式参数；
    这里将权重读取集中在一起，方便后续升级而不影响调用方。
    """
    return {
        "a": _get_scheduler_numeric_config("PRIORITY_WEIGHT_A", 1.0),
        "b": _get_scheduler_numeric_config("PRIORITY_WEIGHT_B", 0.5),
        "c": _get_scheduler_numeric_config("PRIORITY_WEIGHT_C", 1.0),
        "d": _get_scheduler_numeric_config("PRIORITY_WEIGHT_D", 0.3),
        "e": _get_scheduler_numeric_config("PRIORITY_WEIGHT_E", 0.8),
    }


def _call_ahead_seconds() -> int:
    return int(_get_scheduler_numeric_config("T_CALL_MINUTES", 5) * 60)


def waiting_pool_for_mode(charge_mode: str) -> str:
    return (
        WaitingPoolType.FAST_POOL.value
        if charge_mode == ChargeMode.FAST.value
        else WaitingPoolType.SLOW_POOL.value
    )


def _anchor_time(event_time: Optional[str] = None) -> datetime:
    return parse_datetime(event_time, fallback=datetime.now())


def _load_runtime_stations(scenario_id: int, anchor_time: datetime) -> Dict[str, List[RuntimeStation]]:
    rows = query_db(
        """
        SELECT id, station_code, station_type, power_kw, status, available_time
        FROM charging_station
        WHERE scenario_id = ?
        ORDER BY station_type, station_code
        """,
        [scenario_id],
    )

    grouped: Dict[str, List[RuntimeStation]] = {
        ChargeMode.FAST.value: [],
        ChargeMode.SLOW.value: [],
    }

    for row in rows or []:
        row_dict = dict(row)
        if row_dict["status"] == StationStatus.FAULT.value:
            continue

        available_at = parse_datetime(row_dict.get("available_time"), fallback=anchor_time)
        if available_at < anchor_time:
            available_at = anchor_time

        grouped[row_dict["station_type"]].append(
            RuntimeStation(
                station_id=row_dict["id"],
                station_code=row_dict["station_code"],
                station_type=row_dict["station_type"],
                power_kw=float(row_dict["power_kw"]),
                available_at=available_at,
                status=row_dict["status"],
            )
        )

    return grouped


def _load_waiting_requests(scenario_id: int, pool_type: str) -> List[Dict[str, Any]]:
    rows = query_db(
        """
        SELECT id, request_id, charge_mode, request_energy, submit_time,
               estimated_service_seconds, priority_score, waiting_pool_type,
               retry_count, no_show_count, fault_requeue_flag
        FROM charge_request
        WHERE scenario_id = ?
          AND waiting_pool_type = ?
          AND status IN (?, ?)
        ORDER BY submit_time ASC, id ASC
        """,
        [
            scenario_id,
            pool_type,
            RequestStatus.WAITING.value,
            RequestStatus.FAULT_REQUEUE.value,
        ],
    )
    return [dict(row) for row in rows] if rows else []


def _score_waiting_request(
    req: Dict[str, Any],
    anchor_time: datetime,
    default_power_kw: Optional[float],
    weights: Dict[str, float],
) -> float:
    """
    计算等待请求的优先级分数。

    当前实现采用“等待时间 + 补偿 - 服务时长 - 过号惩罚”的可扩展形式，
    与文档语义对齐，同时保留后续继续细化的空间。
    """
    submit_time = parse_datetime(req["submit_time"], fallback=anchor_time)
    wait_minutes = max(0.0, (anchor_time - submit_time).total_seconds() / 60.0)
    service_minutes = (
        float(req.get("estimated_service_seconds") or service_seconds_for_request(
            req["request_energy"],
            req["charge_mode"],
            default_power_kw,
        )) / 60.0
    )
    retry_bonus = float(req.get("retry_count") or 0) * 5.0
    fault_bonus = 10.0 if bool(req.get("fault_requeue_flag")) else 0.0
    no_show_penalty = float(req.get("no_show_count") or 0) * 3.0

    score = (
        weights["a"] * wait_minutes
        + weights["b"] * retry_bonus
        + weights["c"] * fault_bonus
        - weights["d"] * service_minutes
        - weights["e"] * no_show_penalty
    )
    return round(score, 4)


def _choose_best_station(
    runtime_stations: List[RuntimeStation],
    submit_time: datetime,
    anchor_time: datetime,
    request_energy: float,
    charge_mode: str,
) -> Tuple[RuntimeStation, int, datetime, datetime, int]:
    """
    为当前请求选择预测完成时间最优的充电桩。

    这样后续如果要升级为更复杂的选桩策略，只需替换本函数。
    """
    candidates: List[Tuple[datetime, datetime, str, RuntimeStation, int]] = []

    for station in runtime_stations:
        service_seconds = service_seconds_for_request(request_energy, charge_mode, station.power_kw)
        start_time = max(anchor_time, submit_time, station.available_at)
        finish_time = start_time + timedelta(seconds=service_seconds)
        candidates.append((finish_time, start_time, station.station_code, station, service_seconds))

    finish_time, start_time, _, station, service_seconds = min(candidates, key=lambda item: (item[0], item[1], item[2]))
    wait_seconds = max(0, int((start_time - submit_time).total_seconds()))
    return station, wait_seconds, start_time, finish_time, service_seconds


def _predict_pool_requests(
    requests: List[Dict[str, Any]],
    stations: List[RuntimeStation],
    anchor_time: datetime,
) -> List[RuntimePrediction]:
    """对同一等待池内的请求执行最早可用桩分配预测。"""
    if not requests:
        return []

    weights = _load_priority_weights()
    default_power_kw = stations[0].power_kw if stations else None
    prepared_requests = []
    for req in requests:
        enriched = dict(req)
        enriched["priority_score"] = _score_waiting_request(req, anchor_time, default_power_kw, weights)
        prepared_requests.append(enriched)
    prepared_requests.sort(
        key=lambda req: (
            -float(req["priority_score"]),
            parse_datetime(req["submit_time"], fallback=anchor_time),
            req["id"],
        )
    )

    if not stations:
        return [
            RuntimePrediction(
                id=req["id"],
                request_id=req["request_id"],
                queue_position=index + 1,
                estimated_wait_seconds=None,
                estimated_start_time=None,
                estimated_finish_time=None,
                estimated_service_seconds=req.get("estimated_service_seconds")
                or service_seconds_for_request(req["request_energy"], req["charge_mode"]),
                recommended_station_id=None,
                recommended_station_code=None,
                priority_score=float(req["priority_score"]),
            )
            for index, req in enumerate(prepared_requests)
        ]

    runtime_stations = [
        RuntimeStation(
            station_id=station.station_id,
            station_code=station.station_code,
            station_type=station.station_type,
            power_kw=station.power_kw,
            available_at=station.available_at,
            status=station.status,
            busy_seconds=station.busy_seconds,
        )
        for station in stations
    ]

    predictions: List[RuntimePrediction] = []

    for index, req in enumerate(prepared_requests):
        submit_time = parse_datetime(req["submit_time"], fallback=anchor_time)
        chosen_station, wait_seconds, start_time, finish_time, service_seconds = _choose_best_station(
            runtime_stations,
            submit_time,
            anchor_time,
            float(req["request_energy"]),
            req["charge_mode"],
        )

        predictions.append(
            RuntimePrediction(
                id=req["id"],
                request_id=req["request_id"],
                queue_position=index + 1,
                estimated_wait_seconds=wait_seconds,
                estimated_start_time=start_time,
                estimated_finish_time=finish_time,
                estimated_service_seconds=service_seconds,
                recommended_station_id=chosen_station.station_id,
                recommended_station_code=chosen_station.station_code,
                priority_score=float(req["priority_score"]),
            )
        )

        chosen_station.available_at = finish_time

    return predictions


def _build_call_recommendation(
    predictions: List[RuntimePrediction],
    anchor_time: datetime,
) -> Optional[Dict[str, Any]]:
    """
    生成当前时刻的叫号建议。

    当前调用方暂未强依赖该结果，但保留该结构可以方便后续将简化状态机
    升级为文档中的完整叫号机制，而不必改动重调度入口。
    """
    threshold_seconds = _call_ahead_seconds()
    eligible: List[RuntimePrediction] = []
    for prediction in predictions:
        if not prediction.recommended_station_code or not prediction.estimated_start_time:
            continue
        delta = (prediction.estimated_start_time - anchor_time).total_seconds()
        if delta <= threshold_seconds:
            eligible.append(prediction)

    if not eligible:
        return None

    target = min(
        eligible,
        key=lambda item: (
            item.estimated_start_time or anchor_time,
            item.queue_position,
            item.request_id,
        ),
    )
    return {
        "request_id": target.request_id,
        "station_code": target.recommended_station_code,
        "call_before_seconds": threshold_seconds,
        "estimated_start_time": format_datetime(target.estimated_start_time),
    }


def reschedule_waiting_requests(
    scenario_id: int,
    event_type: Optional[str] = None,
    event_time: Optional[str] = None,
) -> Dict[str, Any]:
    """
    关键事件后的统一重调度入口。

    当前阶段按文档约定，采用全量重算。
    """
    anchor_time = _anchor_time(event_time)
    stations_by_mode = _load_runtime_stations(scenario_id, anchor_time)

    fast_predictions = _predict_pool_requests(
        _load_waiting_requests(scenario_id, WaitingPoolType.FAST_POOL.value),
        stations_by_mode[ChargeMode.FAST.value],
        anchor_time,
    )
    slow_predictions = _predict_pool_requests(
        _load_waiting_requests(scenario_id, WaitingPoolType.SLOW_POOL.value),
        stations_by_mode[ChargeMode.SLOW.value],
        anchor_time,
    )

    all_predictions = fast_predictions + slow_predictions
    updated_ids: List[str] = []
    for prediction in all_predictions:
        execute_db(
            """
            UPDATE charge_request
            SET estimated_wait_seconds = ?,
                estimated_start_time = ?,
                estimated_finish_time = ?,
                estimated_service_seconds = ?,
                assigned_station_id = ?,
                priority_score = ?,
                updated_at = ?
            WHERE id = ?
            """,
            [
                prediction.estimated_wait_seconds,
                format_datetime(prediction.estimated_start_time),
                format_datetime(prediction.estimated_finish_time),
                prediction.estimated_service_seconds,
                prediction.recommended_station_id,
                prediction.priority_score,
                format_datetime(anchor_time),
                prediction.id,
            ],
        )
        updated_ids.append(prediction.request_id)

    call_recommendation = _build_call_recommendation(all_predictions, anchor_time)

    return {
        "event_type": event_type,
        "event_time": format_datetime(anchor_time),
        "updated_request_ids": updated_ids,
        "updated_count": len(updated_ids),
        "should_call": call_recommendation is not None,
        "call_recommendation": call_recommendation,
    }


def predict_request_by_id(request_id: str, event_time: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """重调度后读取指定请求的最新预测结果。"""
    req = query_db(
        """
        SELECT request_id, status, estimated_wait_seconds, estimated_start_time,
               estimated_finish_time, waiting_pool_type, assigned_station_id
        FROM charge_request
        WHERE request_id = ?
        """,
        [request_id],
        one=True,
    )
    if not req:
        return None

    req_dict = dict(req)
    if req_dict["waiting_pool_type"] and req_dict["status"] in (
        RequestStatus.WAITING.value,
        RequestStatus.FAULT_REQUEUE.value,
    ):
        position = query_db(
            """
            SELECT COUNT(*) AS cnt
            FROM charge_request
            WHERE waiting_pool_type = ?
              AND status IN (?, ?)
              AND (
                    priority_score > (
                        SELECT priority_score FROM charge_request WHERE request_id = ?
                    )
                    OR (
                        priority_score = (
                            SELECT priority_score FROM charge_request WHERE request_id = ?
                        )
                        AND submit_time < (
                            SELECT submit_time FROM charge_request WHERE request_id = ?
                        )
                    )
              )
            """,
            [
                req_dict["waiting_pool_type"],
                RequestStatus.WAITING.value,
                RequestStatus.FAULT_REQUEUE.value,
                request_id,
                request_id,
                request_id,
            ],
            one=True,
        )
        req_dict["queue_position"] = (position["cnt"] + 1) if position else 1
    else:
        req_dict["queue_position"] = None

    station_code = None
    if req_dict["assigned_station_id"]:
        station = query_db(
            "SELECT station_code FROM charging_station WHERE id = ?",
            [req_dict["assigned_station_id"]],
            one=True,
        )
        station_code = station["station_code"] if station else None

    return {
        "request_id": req_dict["request_id"],
        "status": req_dict["status"],
        "waiting_pool_type": req_dict["waiting_pool_type"],
        "queue_position": req_dict["queue_position"],
        "estimated_wait_seconds": req_dict["estimated_wait_seconds"],
        "estimated_start_time": req_dict["estimated_start_time"],
        "estimated_finish_time": req_dict["estimated_finish_time"],
        "recommended_station_id": station_code,
        "event_time": event_time,
    }


def trigger_reschedule_for_event(
    scenario_id: int,
    event_type: EventType,
    event_time: Optional[str] = None,
) -> Dict[str, Any]:
    return reschedule_waiting_requests(scenario_id, event_type=event_type.value, event_time=event_time)


def advance_request_state_for_status_view(request_ref: Any, now: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """
    供状态查询使用的最小状态推进器。

    目前保留 04-02 联调阶段所需的简化自动推进行为，但收口到服务层，
    方便后续逐步替换为更完整的叫号/充电状态机，而不把逻辑散落在路由里。
    """
    now = now or datetime.now()

    if isinstance(request_ref, dict):
        lookup_value = request_ref.get("id")
        lookup_field = "id"
    elif isinstance(request_ref, int):
        lookup_value = request_ref
        lookup_field = "id"
    else:
        lookup_value = request_ref
        lookup_field = "request_id"

    current = query_db(
        f"SELECT * FROM charge_request WHERE {lookup_field} = ?",
        [lookup_value],
        one=True,
    )
    if not current:
        return None

    current = dict(current)
    status = current["status"]
    estimated_start_dt = parse_datetime(current.get("estimated_start_time"))
    estimated_finish_dt = parse_datetime(current.get("estimated_finish_time"))

    if status == RequestStatus.WAITING.value and current.get("assigned_station_id") and estimated_start_dt:
        called_at = max(now, estimated_start_dt - timedelta(seconds=_call_ahead_seconds()))
        if now >= called_at:
            execute_db(
                """
                UPDATE charge_request
                SET status = 'CALLED',
                    last_called_at = COALESCE(last_called_at, ?),
                    updated_at = ?
                WHERE id = ?
                """,
                [
                    format_datetime(called_at),
                    format_datetime(now),
                    current["id"],
                ],
            )
            current["status"] = RequestStatus.CALLED.value
            current["last_called_at"] = format_datetime(called_at)

    if current["status"] == RequestStatus.CHARGING.value and current.get("assigned_station_id") and estimated_finish_dt and now >= estimated_finish_dt:
        session = query_db(
            """
            SELECT * FROM charging_session
            WHERE request_id = ? AND status = 'CHARGING'
            ORDER BY id DESC
            LIMIT 1
            """,
            [current["id"]],
            one=True,
        )
        if session:
            execute_db(
                """
                UPDATE charging_session
                SET end_time = ?, actual_energy = ?, status = 'COMPLETED'
                WHERE id = ?
                """,
                [
                    format_datetime(estimated_finish_dt),
                    current["request_energy"],
                    session["id"],
                ],
            )

        execute_db(
            """
            UPDATE charge_request
            SET status = 'COMPLETED',
                actual_energy = ?,
                actual_service_seconds = ?,
                updated_at = ?
            WHERE id = ?
            """,
            [
                current["request_energy"],
                current.get("estimated_service_seconds") or 0,
                format_datetime(now),
                current["id"],
            ],
        )
        execute_db(
            """
            UPDATE charging_station
            SET status = 'WAITING_TO_LEAVE',
                current_request_id = ?
            WHERE id = ?
            """,
            [
                current["id"],
                current["assigned_station_id"],
            ],
        )

    refreshed = query_db(
        "SELECT * FROM charge_request WHERE id = ?",
        [current["id"]],
        one=True,
    )
    return dict(refreshed) if refreshed else current


def _create_runtime_stations_for_batch(scenario: Dict[str, Any], base_time: datetime) -> Dict[str, List[RuntimeStation]]:
    grouped: Dict[str, List[RuntimeStation]] = {
        ChargeMode.FAST.value: [],
        ChargeMode.SLOW.value: [],
    }

    snapshots = scenario.get("station_snapshots") or []
    if snapshots:
        for snapshot in snapshots:
            status = snapshot.get("status", StationStatus.IDLE.value)
            available_at = base_time
            remaining_seconds = int(snapshot.get("current_user_remaining_seconds") or 0)
            if status in (StationStatus.CHARGING.value, StationStatus.WAITING_TO_LEAVE.value) and remaining_seconds > 0:
                available_at = base_time + timedelta(seconds=remaining_seconds)
            grouped[snapshot["station_type"]].append(
                RuntimeStation(
                    station_id=None,
                    station_code=snapshot["station_code"],
                    station_type=snapshot["station_type"],
                    power_kw=FAST_POWER_KW if snapshot["station_type"] == ChargeMode.FAST.value else SLOW_POWER_KW,
                    available_at=available_at,
                    status=status,
                )
            )
    else:
        for index in range(int(scenario.get("fast_station_count", 0))):
            grouped[ChargeMode.FAST.value].append(
                RuntimeStation(
                    station_id=None,
                    station_code=f"FAST_{index + 1:02d}",
                    station_type=ChargeMode.FAST.value,
                    power_kw=FAST_POWER_KW,
                    available_at=base_time,
                    status=StationStatus.IDLE.value,
                )
            )
        for index in range(int(scenario.get("slow_station_count", 0))):
            grouped[ChargeMode.SLOW.value].append(
                RuntimeStation(
                    station_id=None,
                    station_code=f"SLOW_{index + 1:02d}",
                    station_type=ChargeMode.SLOW.value,
                    power_kw=SLOW_POWER_KW,
                    available_at=base_time,
                    status=StationStatus.IDLE.value,
                )
            )

    return grouped


def _seed_snapshot_backlog(
    scenario: Dict[str, Any],
    stations_by_mode: Dict[str, List[RuntimeStation]],
    base_time: datetime,
) -> List[Dict[str, Any]]:
    """将桩级快照中的 queue_length 转成初始 backlog。"""
    seeded: List[Dict[str, Any]] = []
    snapshots = scenario.get("station_snapshots") or []

    for snapshot in snapshots:
        queue_length = int(snapshot.get("queue_length") or 0)
        if queue_length <= 0:
            continue

        target_station = None
        for station in stations_by_mode[snapshot["station_type"]]:
            if station.station_code == snapshot["station_code"]:
                target_station = station
                break
        if target_station is None:
            continue

        for index in range(queue_length):
            submit_time = base_time - timedelta(seconds=queue_length - index)
            service_seconds = service_seconds_for_request(
                DEFAULT_VIRTUAL_REQUEST_ENERGY,
                snapshot["station_type"],
                target_station.power_kw,
            )
            start_time = max(target_station.available_at, submit_time)
            finish_time = start_time + timedelta(seconds=service_seconds)
            target_station.available_at = finish_time
            target_station.busy_seconds += service_seconds
            seeded.append(
                {
                    "request_id": f"VIRTUAL_{snapshot['station_code']}_{index + 1:02d}",
                    "status": RequestStatus.COMPLETED.value,
                    "submit_time": format_datetime(submit_time),
                    "estimated_wait_seconds": max(0, int((start_time - submit_time).total_seconds())),
                    "estimated_start_time": format_datetime(start_time),
                    "estimated_finish_time": format_datetime(finish_time),
                    "actual_start_time": format_datetime(start_time),
                    "actual_finish_time": format_datetime(finish_time),
                    "assigned_station_id": snapshot["station_code"],
                    "request_energy": DEFAULT_VIRTUAL_REQUEST_ENERGY,
                    "actual_energy": DEFAULT_VIRTUAL_REQUEST_ENERGY,
                    "count_waiting_area": submit_time < start_time,
                }
            )

    return seeded


def _waiting_occupancy_at(
    timeline: Iterable[Dict[str, Any]],
    at_time: datetime,
) -> int:
    count = 0
    for record in timeline:
        if not record.get("count_waiting_area", False):
            continue
        submit_time = parse_datetime(record.get("submit_time"), fallback=at_time)
        start_time = parse_datetime(record.get("actual_start_time") or record.get("estimated_start_time"), fallback=at_time)
        if submit_time <= at_time < start_time:
            count += 1
    return count


def _build_detail_and_bill(
    request_id: str,
    user_id: str,
    charge_mode: str,
    request_energy: float,
    status: str,
    submit_time: datetime,
    estimated_wait_seconds: Optional[int],
    estimated_start_time: Optional[datetime],
    estimated_finish_time: Optional[datetime],
    actual_start_time: Optional[datetime],
    actual_finish_time: Optional[datetime],
    actual_energy: float,
    station_code: Optional[str],
    note: Optional[str] = None,
) -> Dict[str, Any]:
    energy_fee = round(actual_energy * ENERGY_PRICE, 2)
    bill = {
        "request_id": request_id,
        "billing_energy": round(actual_energy, 2),
        "energy_fee": energy_fee,
        "time_fee": 0.0,
        "occupancy_fee": 0.0,
        "total_fee": energy_fee,
        "payment_status": "UNPAID" if actual_energy > 0 else "UNPAID",
    }

    detail = {
        "request_id": request_id,
        "user_id": user_id,
        "charge_mode": charge_mode,
        "request_energy": request_energy,
        "status": status,
        "submit_time": format_datetime(submit_time),
        "estimated_wait_seconds": estimated_wait_seconds,
        "estimated_start_time": format_datetime(estimated_start_time),
        "estimated_finish_time": format_datetime(estimated_finish_time),
        "actual_start_time": format_datetime(actual_start_time),
        "actual_finish_time": format_datetime(actual_finish_time),
        "actual_energy": round(actual_energy, 2),
        "station_id": station_code,
    }
    if note:
        detail["note"] = note
        bill["note"] = note

    return {"detail": detail, "bill": bill}


def simulate_batch_case(
    test_case_id: str,
    scenario: Dict[str, Any],
    users: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    批量模拟执行引擎。

    当前阶段采用文档中允许的“逐事件回放 + 全量/顺序重算”思路，
    重点保证输入结构、时间排序和关键统计指标可用。
    """
    if users:
        base_time = min(parse_datetime(user["request_time"]) for user in users)
    else:
        base_time = datetime.now()

    sorted_users = sorted(users, key=lambda user: parse_datetime(user["request_time"]))
    stations_by_mode = _create_runtime_stations_for_batch(scenario, base_time)
    simulation_timeline = _seed_snapshot_backlog(scenario, stations_by_mode, base_time)
    results: List[Dict[str, Any]] = []

    waiting_area_capacity = int(scenario.get("waiting_area_capacity", 0))

    for index, user in enumerate(sorted_users, start=1):
        request_time = parse_datetime(user["request_time"], fallback=base_time)
        charge_mode = user["charge_mode"]
        stations = stations_by_mode.get(charge_mode, [])
        request_id = f"{test_case_id}_{index:03d}"
        user_id = user.get("user_id", f"U{index:03d}")
        request_energy = float(user["request_energy"])

        waiting_occupancy = _waiting_occupancy_at(simulation_timeline, request_time)
        if waiting_area_capacity >= 0 and waiting_occupancy >= waiting_area_capacity:
            assembled = _build_detail_and_bill(
                request_id=request_id,
                user_id=user_id,
                charge_mode=charge_mode,
                request_energy=request_energy,
                status="REJECTED_WAITING_AREA_FULL",
                submit_time=request_time,
                estimated_wait_seconds=None,
                estimated_start_time=None,
                estimated_finish_time=None,
                actual_start_time=None,
                actual_finish_time=None,
                actual_energy=0.0,
                station_code=None,
                note="等待区容量已满，当前请求未进入调度队列",
            )
            results.append({"user_id": user_id, "status": "FAILED", **assembled})
            continue

        if not stations:
            assembled = _build_detail_and_bill(
                request_id=request_id,
                user_id=user_id,
                charge_mode=charge_mode,
                request_energy=request_energy,
                status="REJECTED_NO_STATION",
                submit_time=request_time,
                estimated_wait_seconds=None,
                estimated_start_time=None,
                estimated_finish_time=None,
                actual_start_time=None,
                actual_finish_time=None,
                actual_energy=0.0,
                station_code=None,
                note="当前场景不存在匹配的充电桩类型",
            )
            results.append({"user_id": user_id, "status": "FAILED", **assembled})
            continue

        chosen_station = min(stations, key=lambda station: (station.available_at, station.station_code))
        estimated_service_seconds = service_seconds_for_request(request_energy, charge_mode, chosen_station.power_kw)
        estimated_start_time = max(request_time, chosen_station.available_at)
        estimated_finish_time = estimated_start_time + timedelta(seconds=estimated_service_seconds)
        estimated_wait_seconds = max(0, int((estimated_start_time - request_time).total_seconds()))

        cancel_queue = bool(user.get("cancel_queue"))
        cancel_time = parse_datetime(user.get("cancel_time"), fallback=request_time) if cancel_queue else None

        if cancel_queue and cancel_time < estimated_start_time:
            simulation_timeline.append(
                {
                    "request_id": request_id,
                    "submit_time": format_datetime(request_time),
                    "estimated_start_time": format_datetime(estimated_start_time),
                    "actual_start_time": format_datetime(estimated_start_time),
                    "count_waiting_area": True,
                }
            )
            assembled = _build_detail_and_bill(
                request_id=request_id,
                user_id=user_id,
                charge_mode=charge_mode,
                request_energy=request_energy,
                status=RequestStatus.CANCELLED.value,
                submit_time=request_time,
                estimated_wait_seconds=estimated_wait_seconds,
                estimated_start_time=estimated_start_time,
                estimated_finish_time=estimated_finish_time,
                actual_start_time=None,
                actual_finish_time=None,
                actual_energy=0.0,
                station_code=chosen_station.station_code,
                note="用户在预计开始充电前取消排队",
            )
            results.append({"user_id": user_id, "status": RequestStatus.CANCELLED.value, **assembled})
            continue

        confirm_delay_seconds = int(user.get("confirm_arrival_delay_seconds") or 0)
        call_time = max(request_time, estimated_start_time - timedelta(seconds=DEFAULT_CALL_AHEAD_SECONDS))
        confirm_time = call_time + timedelta(seconds=confirm_delay_seconds)

        if confirm_delay_seconds > DEFAULT_CONFIRM_TIMEOUT_SECONDS:
            reserved_until = estimated_start_time
            if chosen_station.available_at < reserved_until:
                chosen_station.available_at = reserved_until
            simulation_timeline.append(
                {
                    "request_id": request_id,
                    "submit_time": format_datetime(request_time),
                    "estimated_start_time": format_datetime(estimated_start_time),
                    "actual_start_time": format_datetime(estimated_start_time),
                    "count_waiting_area": True,
                }
            )
            assembled = _build_detail_and_bill(
                request_id=request_id,
                user_id=user_id,
                charge_mode=charge_mode,
                request_energy=request_energy,
                status=RequestStatus.NO_SHOW.value,
                submit_time=request_time,
                estimated_wait_seconds=estimated_wait_seconds,
                estimated_start_time=estimated_start_time,
                estimated_finish_time=estimated_finish_time,
                actual_start_time=None,
                actual_finish_time=None,
                actual_energy=0.0,
                station_code=chosen_station.station_code,
                note="用户确认到场超时，按过号处理",
            )
            results.append({"user_id": user_id, "status": RequestStatus.NO_SHOW.value, **assembled})
            continue

        interrupt_charge = bool(user.get("interrupt_charge"))
        interrupt_time = parse_datetime(user.get("interrupt_time"), fallback=estimated_finish_time) if interrupt_charge else None

        actual_start_time = estimated_start_time
        actual_finish_time = estimated_finish_time
        actual_energy = request_energy
        final_status = RequestStatus.COMPLETED.value

        if interrupt_charge and interrupt_time > actual_start_time:
            actual_finish_time = min(interrupt_time, estimated_finish_time)
            actual_service_seconds = max(0, int((actual_finish_time - actual_start_time).total_seconds()))
            actual_energy = round(chosen_station.power_kw * actual_service_seconds / 3600, 2)
            final_status = RequestStatus.INTERRUPTED.value

        leave_delay_seconds = int(user.get("leave_delay_seconds") or DEFAULT_LEAVE_DELAY_SECONDS)
        chosen_station.available_at = actual_finish_time + timedelta(seconds=leave_delay_seconds)
        chosen_station.busy_seconds += max(0, int((actual_finish_time - actual_start_time).total_seconds()))

        simulation_timeline.append(
            {
                "request_id": request_id,
                "submit_time": format_datetime(request_time),
                "estimated_start_time": format_datetime(estimated_start_time),
                "actual_start_time": format_datetime(actual_start_time),
                "count_waiting_area": request_time < actual_start_time,
            }
        )

        assembled = _build_detail_and_bill(
            request_id=request_id,
            user_id=user_id,
            charge_mode=charge_mode,
            request_energy=request_energy,
            status=final_status,
            submit_time=request_time,
            estimated_wait_seconds=estimated_wait_seconds,
            estimated_start_time=estimated_start_time,
            estimated_finish_time=estimated_finish_time,
            actual_start_time=actual_start_time,
            actual_finish_time=actual_finish_time,
            actual_energy=actual_energy,
            station_code=chosen_station.station_code,
            note=(
                "用户正常完成充电"
                if final_status == RequestStatus.COMPLETED.value
                else "用户在充电过程中主动中断"
            ),
        )
        results.append({"user_id": user_id, "status": final_status, **assembled})

    service_results = [
        result for result in results if result["status"] in (
            RequestStatus.COMPLETED.value,
            RequestStatus.COMPLETED_EARLY.value,
            RequestStatus.INTERRUPTED.value,
        )
    ]
    wait_samples = [
        result["detail"]["estimated_wait_seconds"]
        for result in results
        if result["detail"].get("estimated_wait_seconds") is not None
    ]
    finish_samples = [
        int(
            (
                parse_datetime(result["detail"]["actual_finish_time"])
                - parse_datetime(result["detail"]["submit_time"])
            ).total_seconds()
        )
        for result in service_results
        if result["detail"].get("actual_finish_time")
    ]

    all_stations = stations_by_mode[ChargeMode.FAST.value] + stations_by_mode[ChargeMode.SLOW.value]
    busy_seconds = sum(station.busy_seconds for station in all_stations)
    if results:
        simulation_start = min(parse_datetime(result["detail"]["submit_time"]) for result in results)
        simulation_end = max(station.available_at for station in all_stations) if all_stations else simulation_start
        makespan_seconds = max(1, int((simulation_end - simulation_start).total_seconds()))
    else:
        makespan_seconds = 1

    summary = {
        "total_users": len(results),
        "completed_users": len(service_results),
        "failed_users": sum(1 for result in results if result["status"] == "FAILED"),
        "avg_wait_seconds": round(sum(wait_samples) / len(wait_samples), 2) if wait_samples else 0,
        "avg_finish_seconds": round(sum(finish_samples) / len(finish_samples), 2) if finish_samples else 0,
        "total_finish_seconds": sum(finish_samples),
        "station_utilization": round(
            busy_seconds / (makespan_seconds * max(1, len(all_stations))),
            4,
        ),
    }

    return {
        "test_case_id": test_case_id,
        "summary": summary,
        "results": results,
    }
