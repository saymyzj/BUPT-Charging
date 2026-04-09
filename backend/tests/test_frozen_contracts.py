"""
冻结接口契约测试

重点验证：
1. 批量模拟输出结构严格对齐冻结文档
2. request/status 响应字段固定
3. confirm_arrival 保持冻结响应语义，同时主流程仍可闭环推进
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.routes.batch_simulate import batch_bp
from app.routes.request import request_bp
from app.utils.db import execute_db, init_db, query_db


class FrozenContractTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["DATABASE_PATH"] = self.db_path
        self.app.register_blueprint(request_bp, url_prefix="/api/request")
        self.app.register_blueprint(batch_bp, url_prefix="/api/batch")
        init_db(self.app)
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_status_response_uses_frozen_fields_only(self):
        request_time = "2026-04-09T10:00:00"
        create_resp = self.client.post(
            "/api/request/create",
            json={
                "request_time": request_time,
                "charge_mode": "FAST",
                "request_energy": 20.0,
            },
        )
        self.assertEqual(create_resp.status_code, 200)
        request_id = create_resp.get_json()["data"]["request_id"]

        status_resp = self.client.get(f"/api/request/status/{request_id}")
        payload = status_resp.get_json()["data"]
        self.assertEqual(
            set(payload.keys()),
            {"request_id", "status", "station_id", "estimated_wait_seconds", "last_called_time"},
        )

    def test_confirm_arrival_keeps_frozen_response_and_can_progress_to_charging(self):
        request_time = datetime(2026, 4, 9, 10, 0, 0)
        create_resp = self.client.post(
            "/api/request/create",
            json={
                "request_time": request_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "charge_mode": "FAST",
                "request_energy": 20.0,
            },
        )
        request_id = create_resp.get_json()["data"]["request_id"]
        called_start = request_time + timedelta(minutes=1)
        finish_time = called_start + timedelta(minutes=40)

        with self.app.app_context():
            execute_db(
                """
                UPDATE charge_request
                SET status = 'WAITING',
                    estimated_start_time = ?,
                    estimated_finish_time = ?,
                    assigned_station_id = 1,
                    estimated_wait_seconds = ?
                WHERE request_id = ?
                """,
                [
                    called_start.strftime("%Y-%m-%dT%H:%M:%S"),
                    finish_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    int((called_start - request_time).total_seconds()),
                    request_id,
                ],
            )

        status_resp = self.client.get(f"/api/request/status/{request_id}")
        self.assertEqual(status_resp.get_json()["data"]["status"], "CALLED")

        confirm_resp = self.client.post(
            "/api/request/confirm_arrival",
            json={
                "request_id": request_id,
                "confirm_time": (called_start + timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%S"),
            },
        )
        confirm_payload = confirm_resp.get_json()["data"]
        self.assertEqual(confirm_payload["status"], "CONFIRMED")
        self.assertEqual(set(confirm_payload.keys()), {"request_id", "status", "station_id"})

        with self.app.app_context():
            execute_db(
                "UPDATE charge_request SET estimated_start_time = ?, estimated_finish_time = ? WHERE request_id = ?",
                [
                    (datetime.now() - timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%S"),
                    (datetime.now() + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%S"),
                    request_id,
                ],
            )

        charging_status = self.client.get(f"/api/request/status/{request_id}").get_json()["data"]
        self.assertEqual(charging_status["status"], "CHARGING")

    def test_batch_simulate_returns_frozen_summary_detail_and_bill(self):
        response = self.client.post(
            "/api/batch/simulate",
            json={
                "test_case_id": "BATCH_001",
                "scenario": {
                    "fast_station_count": 1,
                    "slow_station_count": 1,
                    "waiting_area_capacity": 4,
                    "station_queue_mode": "UNIFORM_CAPACITY",
                    "station_queue_capacity": 2,
                },
                "users": [
                    {
                        "user_id": "U001",
                        "request_time": "2026-04-09T10:00:00",
                        "charge_mode": "FAST",
                        "request_energy": 20.0,
                        "cancel_queue": False,
                        "confirm_arrival_delay_seconds": 60,
                        "interrupt_charge": False,
                        "leave_delay_seconds": 120,
                    }
                ],
            },
        )

        data = response.get_json()["data"]
        self.assertEqual(
            set(data["summary"].keys()),
            {
                "total_users",
                "completed_users",
                "avg_wait_seconds",
                "avg_finish_seconds",
                "total_finish_seconds",
                "station_utilization",
            },
        )
        detail = data["results"][0]["detail"]
        bill = data["results"][0]["bill"]
        self.assertEqual(
            set(detail.keys()),
            {
                "request_id",
                "charge_mode",
                "request_energy",
                "actual_energy",
                "request_time",
                "queue_enter_time",
                "called_time",
                "arrival_confirm_time",
                "charge_start_time",
                "charge_end_time",
                "leave_notify_time",
                "final_leave_time",
                "station_id",
                "final_status",
                "is_no_show",
                "is_cancelled",
                "is_interrupted",
                "is_fault_requeue",
                "is_leave_timeout",
            },
        )
        self.assertEqual(
            set(bill.keys()),
            {
                "request_id",
                "billing_mode",
                "request_energy",
                "billing_energy",
                "energy_fee",
                "time_fee",
                "occupancy_fee",
                "total_fee",
                "payment_status",
            },
        )


if __name__ == "__main__":
    unittest.main()
