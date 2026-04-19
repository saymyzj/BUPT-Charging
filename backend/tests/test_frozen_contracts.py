"""V3 Day 3 最小接口契约测试。"""

import os
import sqlite3
import sys
import tempfile
import unittest

from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.batch_simulate import batch_bp
from app.routes.health import health_bp
from app.routes.request import request_bp
from app.routes.stations import stations_bp
from app.services.queue_model import enqueue_request, run_normal_scheduler
from app.utils.db import execute_db, init_db, query_db


class FrozenContractTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["DATABASE_PATH"] = self.db_path
        self.app.config["SECRET_KEY"] = "test-secret"
        self.app.config["JWT_EXPIRATION_HOURS"] = 24
        self.app.config["WAITING_AREA_SIZE"] = 6
        self.app.config["CHARGING_QUEUE_LEN"] = 2
        self.app.config["DISPATCH_MODE"] = "NORMAL"
        self.app.config["FAULT_DISPATCH_MODE"] = "TIME_ORDER"
        self.app.register_blueprint(auth_bp, url_prefix="/api/auth")
        self.app.register_blueprint(health_bp)
        self.app.register_blueprint(admin_bp, url_prefix="/api/admin")
        self.app.register_blueprint(request_bp, url_prefix="/api/request")
        self.app.register_blueprint(stations_bp, url_prefix="/api/stations")
        self.app.register_blueprint(batch_bp, url_prefix="/api/test")
        init_db(self.app)
        self.client = self.app.test_client()

        self.client.post(
            "/api/auth/register",
            json={"username": "user_001", "password": "secret12", "battery_capacity": 60.0},
        )
        login_payload = self.client.post(
            "/api/auth/login",
            json={"username": "user_001", "password": "secret12"},
        ).get_json()
        self.auth_headers = {"Authorization": f"Bearer {login_payload['data']['token']}"}

        self.client.post(
            "/api/auth/register",
            json={
                "username": "admin_001",
                "password": "secret12",
                "battery_capacity": 80.0,
                "role": "ADMIN",
            },
        )
        admin_login = self.client.post(
            "/api/auth/login",
            json={"username": "admin_001", "password": "secret12"},
        ).get_json()
        self.admin_headers = {"Authorization": f"Bearer {admin_login['data']['token']}"}

    def _register_and_login(self, username: str):
        self.client.post(
            "/api/auth/register",
            json={"username": username, "password": "secret12", "battery_capacity": 60.0},
        )
        login_payload = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "secret12"},
        ).get_json()
        return {"Authorization": f"Bearer {login_payload['data']['token']}"}

    def _create_request(self, headers, request_time: str, charge_mode: str, request_energy: float):
        return self.client.post(
            "/api/request/create",
            headers=headers,
            json={
                "request_time": request_time,
                "charge_mode": charge_mode,
                "request_energy": request_energy,
            },
        ).get_json()

    def _set_dispatch_mode(self, mode: str):
        with self.app.app_context():
            execute_db(
                """
                UPDATE scheduler_config
                SET config_value = ?
                WHERE config_key = 'dispatch_mode'
                """,
                [mode],
            )

    def _set_fault_dispatch_mode(self, mode: str):
        with self.app.app_context():
            execute_db(
                """
                UPDATE scheduler_config
                SET config_value = ?
                WHERE config_key = 'fault_dispatch_mode'
                """,
                [mode],
            )

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_create_request_returns_v3_minimal_fields(self):
        payload = self._create_request(
            self.auth_headers,
            "2026-04-19T10:00:00",
            "FAST",
            20.0,
        )["data"]
        self.assertEqual(
            set(payload.keys()),
            {"request_id", "queue_number", "request_status", "front_waiting_count"},
        )
        self.assertEqual(payload["request_status"], "WAITING_AREA")
        self.assertEqual(payload["queue_number"], "F1")
        self.assertEqual(payload["front_waiting_count"], 0)

    def test_health_check_uses_v3_success_envelope(self):
        payload = self.client.get("/api/health").get_json()
        self.assertEqual(payload["code"], 0)
        self.assertEqual(payload["message"], "success")
        self.assertEqual(payload["data"]["status"], "ok")
        self.assertIn("timestamp", payload["data"])

    def test_init_db_rebuilds_legacy_sqlite_schema_with_backup(self):
        fd, legacy_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        backup_paths = []
        try:
            con = sqlite3.connect(legacy_path)
            con.executescript(
                """
                CREATE TABLE charging_station (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_code TEXT,
                    station_type TEXT,
                    status TEXT
                );
                CREATE TABLE charge_request (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT,
                    status TEXT,
                    submit_time TEXT
                );
                CREATE TABLE user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    password_hash TEXT,
                    role TEXT
                );
                CREATE TABLE scheduler_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT,
                    config_value TEXT
                );
                """
            )
            con.commit()
            con.close()

            app = Flask(__name__)
            app.config["TESTING"] = True
            app.config["DATABASE_PATH"] = legacy_path
            app.config["SECRET_KEY"] = "test-secret"
            app.config["WAITING_AREA_SIZE"] = 6
            app.config["CHARGING_QUEUE_LEN"] = 2
            app.config["FAST_CHARGING_PILE_NUM"] = 3
            app.config["TRICKLE_CHARGING_PILE_NUM"] = 2
            app.config["DISPATCH_MODE"] = "NORMAL"
            app.config["FAULT_DISPATCH_MODE"] = "TIME_ORDER"
            app.config["AUTO_REBUILD_INCOMPATIBLE_DB"] = True
            app.register_blueprint(health_bp)
            init_db(app)
            client = app.test_client()

            payload = client.get("/api/health").get_json()
            self.assertEqual(payload["code"], 0)
            self.assertEqual(payload["data"]["status"], "ok")

            con = sqlite3.connect(legacy_path)
            station_columns = {
                row[1]
                for row in con.execute("PRAGMA table_info(charging_station)").fetchall()
            }
            request_columns = {
                row[1]
                for row in con.execute("PRAGMA table_info(charge_request)").fetchall()
            }
            station_count = con.execute("SELECT COUNT(*) FROM charging_station").fetchone()[0]
            con.close()

            self.assertIn("charge_mode", station_columns)
            self.assertIn("station_status", station_columns)
            self.assertIn("request_status", request_columns)
            self.assertIn("queue_number", request_columns)
            self.assertEqual(station_count, 5)

            backup_paths = [
                entry.path
                for entry in os.scandir(os.path.dirname(legacy_path))
                if entry.name.startswith(os.path.basename(legacy_path) + ".legacy-")
            ]
            self.assertEqual(len(backup_paths), 1)
        finally:
            if os.path.exists(legacy_path):
                os.unlink(legacy_path)
            for backup_path in backup_paths:
                if os.path.exists(backup_path):
                    os.unlink(backup_path)

    def test_init_db_rebuilds_corrupted_sqlite_file_with_backup(self):
        fd, broken_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        backup_paths = []
        try:
            with open(broken_path, "wb") as fh:
                fh.write(b"not-a-sqlite-database")

            app = Flask(__name__)
            app.config["TESTING"] = True
            app.config["DATABASE_PATH"] = broken_path
            app.config["SECRET_KEY"] = "test-secret"
            app.config["WAITING_AREA_SIZE"] = 6
            app.config["CHARGING_QUEUE_LEN"] = 2
            app.config["FAST_CHARGING_PILE_NUM"] = 3
            app.config["TRICKLE_CHARGING_PILE_NUM"] = 2
            app.config["DISPATCH_MODE"] = "NORMAL"
            app.config["FAULT_DISPATCH_MODE"] = "TIME_ORDER"
            app.config["AUTO_REBUILD_INCOMPATIBLE_DB"] = True
            app.register_blueprint(health_bp)
            init_db(app)

            payload = app.test_client().get("/api/health").get_json()
            self.assertEqual(payload["code"], 0)
            self.assertEqual(payload["data"]["status"], "ok")

            con = sqlite3.connect(broken_path)
            tables = {
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            }
            con.close()
            self.assertIn("charge_request", tables)
            self.assertIn("scheduler_config", tables)

            backup_paths = [
                entry.path
                for entry in os.scandir(os.path.dirname(broken_path))
                if entry.name.startswith(os.path.basename(broken_path) + ".legacy-")
            ]
            self.assertEqual(len(backup_paths), 1)
        finally:
            if os.path.exists(broken_path):
                os.unlink(broken_path)
            for backup_path in backup_paths:
                if os.path.exists(backup_path):
                    os.unlink(backup_path)

    def test_status_response_uses_v3_fields_only(self):
        create_payload = self._create_request(
            self.auth_headers,
            "2026-04-19T10:00:00",
            "FAST",
            20.0,
        )["data"]

        status_payload = self.client.get(
            f"/api/request/status/{create_payload['request_id']}",
            headers=self.auth_headers,
        ).get_json()["data"]
        self.assertEqual(
            set(status_payload.keys()),
            {
                "request_id",
                "queue_number",
                "charge_mode",
                "request_energy",
                "request_status",
                "front_waiting_count",
                "station_code",
                "station_queue_position",
                "estimated_wait_seconds",
                "estimated_start_time",
                "estimated_finish_time",
            },
        )
        self.assertEqual(status_payload["request_status"], "CHARGING")
        self.assertEqual(status_payload["station_code"], "FAST_01")
        self.assertEqual(status_payload["station_queue_position"], 1)
        self.assertEqual(status_payload["estimated_wait_seconds"], 0)
        self.assertEqual(status_payload["estimated_start_time"], "2026-04-19T10:00:00")
        self.assertEqual(status_payload["estimated_finish_time"], "2026-04-19T10:40:00")

    def test_same_user_cannot_create_second_active_request(self):
        self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)
        second = self._create_request(self.auth_headers, "2026-04-19T10:05:00", "SLOW", 10.0)
        self.assertEqual(second["code"], 1003)

    def test_create_request_rejects_when_all_target_stations_are_unavailable(self):
        with self.app.app_context():
            execute_db("UPDATE charging_station SET station_status = 'FAULT' WHERE charge_mode = 'FAST'")

        payload = self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)
        self.assertEqual(payload["code"], 1005)

    def test_queue_model_uses_fixed_station_queue_capacity(self):
        user2_headers = self._register_and_login("user_002")
        user3_headers = self._register_and_login("user_003")
        user4_headers = self._register_and_login("user_004")

        self._set_dispatch_mode("EXT_SINGLE_BATCH")

        req1 = self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)["data"]["request_id"]
        req2 = self._create_request(user2_headers, "2026-04-19T10:01:00", "FAST", 10.0)["data"]["request_id"]
        req3 = self._create_request(user3_headers, "2026-04-19T10:02:00", "FAST", 5.0)["data"]["request_id"]
        req4 = self._create_request(user4_headers, "2026-04-19T10:03:00", "FAST", 5.0)["data"]["request_id"]

        with self.app.app_context():
            ok1, _ = enqueue_request("FAST_01", req1, "2026-04-19T10:00:00")
            ok2, _ = enqueue_request("FAST_01", req2, "2026-04-19T10:01:00")
            ok3, message3 = enqueue_request("FAST_01", req3, "2026-04-19T10:02:00")

        self.assertTrue(ok1)
        self.assertTrue(ok2)
        self.assertFalse(ok3)
        self.assertNotEqual(message3, "success")

        status_payload = self.client.get(
            f"/api/request/status/{req2}",
            headers=user2_headers,
        ).get_json()["data"]
        self.assertEqual(status_payload["request_status"], "QUEUED")
        self.assertEqual(status_payload["station_code"], "FAST_01")
        self.assertEqual(status_payload["station_queue_position"], 2)
        self.assertEqual(status_payload["estimated_wait_seconds"], 2340)
        self.assertEqual(status_payload["estimated_start_time"], "2026-04-19T10:40:00")
        self.assertEqual(status_payload["estimated_finish_time"], "2026-04-19T11:00:00")

        waiting_payload = self.client.get(
            f"/api/request/status/{req4}",
            headers=user4_headers,
        ).get_json()["data"]
        self.assertEqual(waiting_payload["request_status"], "WAITING_AREA")
        self.assertEqual(waiting_payload["front_waiting_count"], 1)
        self.assertIsNone(waiting_payload["station_code"])
        self.assertIsNone(waiting_payload["station_queue_position"])

    def test_normal_scheduler_prefers_shortest_finish_time(self):
        user2_headers = self._register_and_login("user_002")
        user3_headers = self._register_and_login("user_003")
        user4_headers = self._register_and_login("user_004")

        req1 = self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)["data"]["request_id"]
        req2 = self._create_request(user2_headers, "2026-04-19T10:01:00", "FAST", 20.0)["data"]["request_id"]
        req3 = self._create_request(user3_headers, "2026-04-19T10:02:00", "FAST", 20.0)["data"]["request_id"]
        req4 = self._create_request(user4_headers, "2026-04-19T10:03:00", "FAST", 10.0)["data"]["request_id"]

        status1 = self.client.get(f"/api/request/status/{req1}", headers=self.auth_headers).get_json()["data"]
        status2 = self.client.get(f"/api/request/status/{req2}", headers=user2_headers).get_json()["data"]
        status3 = self.client.get(f"/api/request/status/{req3}", headers=user3_headers).get_json()["data"]
        status4 = self.client.get(f"/api/request/status/{req4}", headers=user4_headers).get_json()["data"]

        self.assertEqual(status1["request_status"], "CHARGING")
        self.assertEqual(status1["station_code"], "FAST_01")
        self.assertEqual(status2["request_status"], "CHARGING")
        self.assertEqual(status2["station_code"], "FAST_02")
        self.assertEqual(status3["request_status"], "CHARGING")
        self.assertEqual(status3["station_code"], "FAST_03")
        self.assertEqual(status4["request_status"], "QUEUED")
        self.assertEqual(status4["station_code"], "FAST_01")
        self.assertEqual(status4["station_queue_position"], 2)
        self.assertEqual(status4["estimated_start_time"], "2026-04-19T10:40:00")
        self.assertEqual(status4["estimated_finish_time"], "2026-04-19T11:00:00")

    def test_normal_scheduler_advances_completion_and_promotes_queue_head(self):
        user2_headers = self._register_and_login("user_002")
        user3_headers = self._register_and_login("user_003")
        user4_headers = self._register_and_login("user_004")

        req1 = self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)["data"]["request_id"]
        self._create_request(user2_headers, "2026-04-19T10:01:00", "FAST", 20.0)
        self._create_request(user3_headers, "2026-04-19T10:02:00", "FAST", 20.0)
        req4 = self._create_request(user4_headers, "2026-04-19T10:03:00", "FAST", 10.0)["data"]["request_id"]

        with self.app.app_context():
            run_normal_scheduler(event_time="2026-04-19T10:40:00", charge_mode="FAST")

        status1 = self.client.get(f"/api/request/status/{req1}", headers=self.auth_headers).get_json()["data"]
        status4 = self.client.get(f"/api/request/status/{req4}", headers=user4_headers).get_json()["data"]

        self.assertEqual(status1["request_status"], "COMPLETED")
        self.assertEqual(status4["request_status"], "CHARGING")
        self.assertEqual(status4["station_code"], "FAST_01")
        self.assertEqual(status4["station_queue_position"], 1)
        self.assertEqual(status4["estimated_start_time"], "2026-04-19T10:40:00")
        self.assertEqual(status4["estimated_finish_time"], "2026-04-19T11:00:00")

    def test_request_detail_uses_time_of_use_billing_fields(self):
        request_id = self._create_request(
            self.auth_headers,
            "2026-04-19T09:50:00",
            "FAST",
            20.0,
        )["data"]["request_id"]

        with self.app.app_context():
            run_normal_scheduler(event_time="2026-04-19T10:30:00", charge_mode="FAST")

        status_payload = self.client.get(
            f"/api/request/status/{request_id}",
            headers=self.auth_headers,
        ).get_json()["data"]
        self.assertEqual(status_payload["request_status"], "COMPLETED")

        detail_payload = self.client.get(
            f"/api/request/detail/{request_id}",
            headers=self.auth_headers,
        ).get_json()["data"]
        self.assertEqual(
            set(detail_payload.keys()),
            {
                "detail_id",
                "detail_generated_at",
                "station_code",
                "actual_energy",
                "charge_duration_seconds",
                "start_time",
                "stop_time",
                "charge_fee",
                "service_fee",
                "total_fee",
                "request_status",
            },
        )
        self.assertEqual(detail_payload["detail_id"], "DETAIL0001")
        self.assertEqual(detail_payload["detail_generated_at"], "2026-04-19T10:30:00")
        self.assertEqual(detail_payload["station_code"], "FAST_01")
        self.assertEqual(detail_payload["actual_energy"], 20.0)
        self.assertEqual(detail_payload["charge_duration_seconds"], 2400)
        self.assertEqual(detail_payload["start_time"], "2026-04-19T09:50:00")
        self.assertEqual(detail_payload["stop_time"], "2026-04-19T10:30:00")
        self.assertEqual(detail_payload["charge_fee"], 18.5)
        self.assertEqual(detail_payload["service_fee"], 16.0)
        self.assertEqual(detail_payload["total_fee"], 34.5)
        self.assertEqual(detail_payload["request_status"], "COMPLETED")

    def test_update_request_mode_moves_waiting_request_to_new_mode_tail(self):
        user2_headers = self._register_and_login("user_002")
        user3_headers = self._register_and_login("user_003")
        self._set_dispatch_mode("EXT_SINGLE_BATCH")

        self._create_request(user2_headers, "2026-04-19T10:00:00", "SLOW", 10.0)
        self._create_request(user3_headers, "2026-04-19T10:01:00", "SLOW", 10.0)
        request_id = self._create_request(
            self.auth_headers,
            "2026-04-19T10:02:00",
            "FAST",
            20.0,
        )["data"]["request_id"]

        payload = self.client.put(
            "/api/request/mode",
            headers=self.auth_headers,
            json={"request_id": request_id, "charge_mode": "SLOW"},
        ).get_json()["data"]
        self.assertEqual(
            payload,
            {
                "request_id": request_id,
                "queue_number": "T3",
                "request_status": "WAITING_AREA",
                "front_waiting_count": 2,
            },
        )

        status_payload = self.client.get(
            f"/api/request/status/{request_id}",
            headers=self.auth_headers,
        ).get_json()["data"]
        self.assertEqual(status_payload["charge_mode"], "SLOW")
        self.assertEqual(status_payload["queue_number"], "T3")
        self.assertEqual(status_payload["request_status"], "WAITING_AREA")
        self.assertEqual(status_payload["front_waiting_count"], 2)

    def test_update_request_energy_keeps_queue_number(self):
        user2_headers = self._register_and_login("user_002")
        self._set_dispatch_mode("EXT_SINGLE_BATCH")

        self._create_request(user2_headers, "2026-04-19T10:00:00", "FAST", 20.0)
        request_id = self._create_request(
            self.auth_headers,
            "2026-04-19T10:01:00",
            "FAST",
            10.0,
        )["data"]["request_id"]

        payload = self.client.put(
            "/api/request/energy",
            headers=self.auth_headers,
            json={"request_id": request_id, "request_energy": 25.0},
        ).get_json()["data"]
        self.assertEqual(
            payload,
            {
                "request_id": request_id,
                "queue_number": "F2",
                "request_energy": 25.0,
                "request_status": "WAITING_AREA",
                "front_waiting_count": 1,
            },
        )

        status_payload = self.client.get(
            f"/api/request/status/{request_id}",
            headers=self.auth_headers,
        ).get_json()["data"]
        self.assertEqual(status_payload["queue_number"], "F2")
        self.assertEqual(status_payload["request_energy"], 25.0)
        self.assertEqual(status_payload["request_status"], "WAITING_AREA")

    def test_cancel_waiting_area_request_sets_cancelled_without_detail(self):
        self._set_dispatch_mode("EXT_SINGLE_BATCH")
        request_id = self._create_request(
            self.auth_headers,
            "2026-04-19T10:00:00",
            "FAST",
            20.0,
        )["data"]["request_id"]

        payload = self.client.post(
            "/api/request/cancel",
            headers=self.auth_headers,
            json={"request_id": request_id},
        ).get_json()["data"]
        self.assertEqual(
            payload,
            {"request_id": request_id, "request_status": "CANCELLED"},
        )

        status_payload = self.client.get(
            f"/api/request/status/{request_id}",
            headers=self.auth_headers,
        ).get_json()["data"]
        self.assertEqual(status_payload["request_status"], "CANCELLED")

        detail_response = self.client.get(
            f"/api/request/detail/{request_id}",
            headers=self.auth_headers,
        ).get_json()
        self.assertEqual(detail_response["code"], 1006)

    def test_stop_queued_request_generates_zero_energy_detail(self):
        user2_headers = self._register_and_login("user_002")
        self._set_dispatch_mode("EXT_SINGLE_BATCH")

        req1 = self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)["data"]["request_id"]
        req2 = self._create_request(user2_headers, "2026-04-19T10:01:00", "FAST", 10.0)["data"]["request_id"]

        with self.app.app_context():
            enqueue_request("FAST_01", req1, "2026-04-19T10:00:00")
            enqueue_request("FAST_01", req2, "2026-04-19T10:01:00")

        payload = self.client.post(
            "/api/request/stop",
            headers=user2_headers,
            json={"request_id": req2, "stop_time": "2026-04-19T10:05:00", "intent": "USER_CANCEL"},
        ).get_json()["data"]
        self.assertEqual(
            payload,
            {"request_id": req2, "request_status": "COMPLETED_EARLY"},
        )

        detail_payload = self.client.get(
            f"/api/request/detail/{req2}",
            headers=user2_headers,
        ).get_json()["data"]
        self.assertEqual(detail_payload["actual_energy"], 0.0)
        self.assertEqual(detail_payload["charge_duration_seconds"], 0)
        self.assertEqual(detail_payload["start_time"], "2026-04-19T10:05:00")
        self.assertEqual(detail_payload["stop_time"], "2026-04-19T10:05:00")
        self.assertEqual(detail_payload["charge_fee"], 0.0)
        self.assertEqual(detail_payload["service_fee"], 0.0)
        self.assertEqual(detail_payload["total_fee"], 0.0)
        self.assertEqual(detail_payload["request_status"], "COMPLETED_EARLY")

    def test_stop_charging_request_generates_partial_detail(self):
        request_id = self._create_request(
            self.auth_headers,
            "2026-04-19T10:00:00",
            "FAST",
            20.0,
        )["data"]["request_id"]

        payload = self.client.post(
            "/api/request/stop",
            headers=self.auth_headers,
            json={"request_id": request_id, "stop_time": "2026-04-19T10:20:00", "intent": "USER_STOP"},
        ).get_json()["data"]
        self.assertEqual(
            payload,
            {"request_id": request_id, "request_status": "COMPLETED_EARLY"},
        )

        detail_payload = self.client.get(
            f"/api/request/detail/{request_id}",
            headers=self.auth_headers,
        ).get_json()["data"]
        self.assertEqual(detail_payload["actual_energy"], 10.0)
        self.assertEqual(detail_payload["charge_duration_seconds"], 1200)
        self.assertEqual(detail_payload["start_time"], "2026-04-19T10:00:00")
        self.assertEqual(detail_payload["stop_time"], "2026-04-19T10:20:00")
        self.assertEqual(detail_payload["charge_fee"], 10.0)
        self.assertEqual(detail_payload["service_fee"], 8.0)
        self.assertEqual(detail_payload["total_fee"], 18.0)
        self.assertEqual(detail_payload["request_status"], "COMPLETED_EARLY")

    def test_admin_can_update_fault_dispatch_mode(self):
        payload = self.client.put(
            "/api/admin/system/fault-dispatch-mode",
            headers=self.admin_headers,
            json={"fault_dispatch_mode": "PRIORITY"},
        ).get_json()["data"]
        self.assertEqual(payload, {"fault_dispatch_mode": "PRIORITY"})

        config_payload = self.client.get(
            "/api/admin/system/config",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(config_payload["fault_dispatch_mode"], "PRIORITY")

    def test_priority_fault_interrupts_current_and_prioritizes_fault_station_tail(self):
        user2_headers = self._register_and_login("user_002")
        user3_headers = self._register_and_login("user_003")
        self._set_dispatch_mode("EXT_SINGLE_BATCH")
        self._set_fault_dispatch_mode("PRIORITY")

        req1 = self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 30.0)["data"]["request_id"]
        req2 = self._create_request(user2_headers, "2026-04-19T10:01:00", "FAST", 30.0)["data"]["request_id"]
        req3 = self._create_request(user3_headers, "2026-04-19T10:02:00", "FAST", 30.0)["data"]["request_id"]

        with self.app.app_context():
            enqueue_request("FAST_01", req1, "2026-04-19T10:00:00")
            enqueue_request("FAST_01", req2, "2026-04-19T10:01:00")
            enqueue_request("FAST_02", req3, "2026-04-19T10:02:00")

        payload = self.client.post(
            "/api/admin/stations/FAST_01/fault",
            headers=self.admin_headers,
            json={"fault_time": "2026-04-19T10:20:00"},
        ).get_json()["data"]
        self.assertEqual(payload["station_code"], "FAST_01")
        self.assertEqual(payload["station_status"], "FAULT")
        self.assertEqual(payload["fault_dispatch_mode"], "PRIORITY")
        self.assertEqual(payload["interrupted_request_id"], req1)
        self.assertIsNotNone(payload["remaining_request_id"])
        self.assertEqual(payload["requeued_request_ids"], [req2])
        self.assertEqual(payload["scheduled"][0]["request_id"], req2)
        self.assertEqual(payload["scheduled"][0]["target_station_code"], "FAST_03")

        detail_payload = self.client.get(
            f"/api/request/detail/{req1}",
            headers=self.auth_headers,
        ).get_json()["data"]
        self.assertEqual(detail_payload["request_status"], "FAULT_INTERRUPTED")
        self.assertEqual(detail_payload["actual_energy"], 10.0)
        self.assertEqual(detail_payload["charge_duration_seconds"], 1200)
        self.assertEqual(detail_payload["charge_fee"], 10.0)
        self.assertEqual(detail_payload["service_fee"], 8.0)
        self.assertEqual(detail_payload["total_fee"], 18.0)

        status2 = self.client.get(f"/api/request/status/{req2}", headers=user2_headers).get_json()["data"]
        self.assertEqual(status2["request_status"], "CHARGING")
        self.assertEqual(status2["station_code"], "FAST_03")
        self.assertEqual(status2["station_queue_position"], 1)

        remaining_status = self.client.get(
            f"/api/request/status/{payload['remaining_request_id']}",
            headers=self.auth_headers,
        ).get_json()["data"]
        self.assertEqual(remaining_status["request_status"], "WAITING_AREA")
        self.assertEqual(remaining_status["request_energy"], 20.0)

    def test_time_order_fault_requeues_unstarted_requests_by_queue_number(self):
        user_headers = [self.auth_headers]
        for index in range(2, 7):
            user_headers.append(self._register_and_login(f"user_{index:03d}"))
        self._set_dispatch_mode("EXT_SINGLE_BATCH")
        self._set_fault_dispatch_mode("TIME_ORDER")

        request_ids = []
        for index, headers in enumerate(user_headers):
            request_ids.append(
                self._create_request(
                    headers,
                    f"2026-04-19T10:0{index}:00",
                    "FAST",
                    30.0,
                )["data"]["request_id"]
            )

        with self.app.app_context():
            enqueue_request("FAST_01", request_ids[0], "2026-04-19T10:00:00")
            enqueue_request("FAST_01", request_ids[1], "2026-04-19T10:01:00")
            enqueue_request("FAST_02", request_ids[2], "2026-04-19T10:02:00")
            enqueue_request("FAST_02", request_ids[3], "2026-04-19T10:03:00")
            enqueue_request("FAST_03", request_ids[4], "2026-04-19T10:04:00")
            enqueue_request("FAST_03", request_ids[5], "2026-04-19T10:05:00")

        payload = self.client.post(
            "/api/admin/stations/FAST_01/fault",
            headers=self.admin_headers,
            json={"fault_time": "2026-04-19T10:16:00"},
        ).get_json()["data"]
        self.assertEqual(payload["fault_dispatch_mode"], "TIME_ORDER")
        self.assertEqual(payload["interrupted_request_id"], request_ids[0])
        self.assertEqual(payload["requeued_request_ids"], [request_ids[1], request_ids[3], request_ids[5]])
        self.assertEqual(
            [item["request_id"] for item in payload["scheduled"]],
            [request_ids[1], request_ids[3]],
        )

        status2 = self.client.get(f"/api/request/status/{request_ids[1]}", headers=user_headers[1]).get_json()["data"]
        status4 = self.client.get(f"/api/request/status/{request_ids[3]}", headers=user_headers[3]).get_json()["data"]
        status6 = self.client.get(f"/api/request/status/{request_ids[5]}", headers=user_headers[5]).get_json()["data"]
        self.assertEqual(status2["station_code"], "FAST_02")
        self.assertEqual(status2["station_queue_position"], 2)
        self.assertEqual(status4["station_code"], "FAST_03")
        self.assertEqual(status4["station_queue_position"], 2)
        self.assertEqual(status6["request_status"], "WAITING_AREA")

    def test_station_recover_reorders_unstarted_requests_by_time_order(self):
        user_headers = [self.auth_headers]
        for index in range(2, 7):
            user_headers.append(self._register_and_login(f"user_{index:03d}"))
        self._set_dispatch_mode("EXT_SINGLE_BATCH")
        self._set_fault_dispatch_mode("TIME_ORDER")

        request_ids = []
        for index, headers in enumerate(user_headers):
            request_ids.append(
                self._create_request(
                    headers,
                    f"2026-04-19T10:0{index}:00",
                    "FAST",
                    30.0,
                )["data"]["request_id"]
            )

        with self.app.app_context():
            enqueue_request("FAST_01", request_ids[0], "2026-04-19T10:00:00")
            enqueue_request("FAST_01", request_ids[1], "2026-04-19T10:01:00")
            enqueue_request("FAST_02", request_ids[2], "2026-04-19T10:02:00")
            enqueue_request("FAST_02", request_ids[3], "2026-04-19T10:03:00")
            enqueue_request("FAST_03", request_ids[4], "2026-04-19T10:04:00")
            enqueue_request("FAST_03", request_ids[5], "2026-04-19T10:05:00")

        self.client.post(
            "/api/admin/stations/FAST_01/fault",
            headers=self.admin_headers,
            json={"fault_time": "2026-04-19T10:16:00"},
        )
        payload = self.client.post(
            "/api/admin/stations/FAST_01/recover",
            headers=self.admin_headers,
            json={"recover_time": "2026-04-19T10:17:00"},
        ).get_json()["data"]
        self.assertEqual(payload["station_code"], "FAST_01")
        self.assertEqual(payload["station_status"], "RUNNING")
        self.assertEqual(
            [item["request_id"] for item in payload["scheduled"]],
            [request_ids[1], request_ids[3], request_ids[5]],
        )

        status2 = self.client.get(f"/api/request/status/{request_ids[1]}", headers=user_headers[1]).get_json()["data"]
        status4 = self.client.get(f"/api/request/status/{request_ids[3]}", headers=user_headers[3]).get_json()["data"]
        status6 = self.client.get(f"/api/request/status/{request_ids[5]}", headers=user_headers[5]).get_json()["data"]
        self.assertEqual(status2["request_status"], "CHARGING")
        self.assertEqual(status2["station_code"], "FAST_01")
        self.assertEqual(status4["request_status"], "QUEUED")
        self.assertEqual(status4["station_code"], "FAST_02")
        self.assertEqual(status6["request_status"], "QUEUED")
        self.assertEqual(status6["station_code"], "FAST_03")

    def test_admin_can_shutdown_idle_station_and_start_it_to_schedule_waiting_request(self):
        user2_headers = self._register_and_login("user_002")
        user3_headers = self._register_and_login("user_003")

        shutdown_payload = self.client.post(
            "/api/admin/stations/SLOW_02/shutdown",
            headers=self.admin_headers,
            json={"shutdown_time": "2026-04-19T10:00:00"},
        ).get_json()["data"]
        self.assertEqual(shutdown_payload["station_code"], "SLOW_02")
        self.assertEqual(shutdown_payload["station_status"], "SHUTDOWN")

        self._create_request(self.auth_headers, "2026-04-19T10:00:00", "SLOW", 10.0)
        self._create_request(user2_headers, "2026-04-19T10:01:00", "SLOW", 10.0)
        req3 = self._create_request(user3_headers, "2026-04-19T10:02:00", "SLOW", 10.0)["data"]["request_id"]
        waiting_status = self.client.get(f"/api/request/status/{req3}", headers=user3_headers).get_json()["data"]
        self.assertEqual(waiting_status["request_status"], "WAITING_AREA")

        start_payload = self.client.post(
            "/api/admin/stations/SLOW_02/start",
            headers=self.admin_headers,
            json={"start_time": "2026-04-19T10:02:00"},
        ).get_json()["data"]
        self.assertEqual(start_payload["station_code"], "SLOW_02")
        self.assertEqual(start_payload["station_status"], "RUNNING")
        self.assertEqual(start_payload["scheduled"][0]["request_id"], req3)

        status3 = self.client.get(f"/api/request/status/{req3}", headers=user3_headers).get_json()["data"]
        self.assertEqual(status3["request_status"], "CHARGING")
        self.assertEqual(status3["station_code"], "SLOW_02")

    def test_admin_cannot_shutdown_busy_station(self):
        self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)

        payload = self.client.post(
            "/api/admin/stations/FAST_01/shutdown",
            headers=self.admin_headers,
            json={"shutdown_time": "2026-04-19T10:05:00"},
        ).get_json()
        self.assertEqual(payload["code"], 1007)

    def test_admin_user_list_detail_and_battery_capacity_update(self):
        request_id = self._create_request(
            self.auth_headers,
            "2026-04-19T09:50:00",
            "FAST",
            20.0,
        )["data"]["request_id"]
        with self.app.app_context():
            run_normal_scheduler(event_time="2026-04-19T10:30:00", charge_mode="FAST")

        users_payload = self.client.get(
            "/api/admin/users?page=1&page_size=10",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(users_payload["total"], 2)
        user_item = next(item for item in users_payload["users"] if item["user_id"] == "U001")
        self.assertEqual(user_item["username"], "user_001")
        self.assertFalse(user_item["has_active_request"])

        detail_payload = self.client.get(
            "/api/admin/users/U001",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(detail_payload["user_id"], "U001")
        self.assertEqual(detail_payload["battery_capacity"], 60.0)
        self.assertEqual(len(detail_payload["historical_details"]), 1)
        self.assertEqual(detail_payload["historical_details"][0]["request_status"], "COMPLETED")
        self.assertEqual(detail_payload["historical_details"][0]["total_fee"], 34.5)
        self.assertEqual(detail_payload["details"], detail_payload["historical_details"])

        update_payload = self.client.put(
            "/api/admin/users/U001/battery-capacity",
            headers=self.admin_headers,
            json={"battery_capacity": 75.0},
        ).get_json()["data"]
        self.assertEqual(update_payload, {"user_id": "U001", "battery_capacity": 75.0, "updated": True})

        updated_detail = self.client.get(
            "/api/admin/users/U001",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(updated_detail["battery_capacity"], 75.0)

        with self.app.app_context():
            event = query_db(
                """
                SELECT event_type, request_id
                FROM scheduler_event_log
                WHERE event_type = 'ADMIN_UPDATE_BATTERY_CAPACITY'
                """,
                one=True,
            )
        self.assertEqual(event["request_id"], "U001")
        self.assertEqual(request_id, "REQ0001")

    def test_admin_cannot_update_battery_capacity_when_user_has_active_request(self):
        self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)

        payload = self.client.put(
            "/api/admin/users/U001/battery-capacity",
            headers=self.admin_headers,
            json={"battery_capacity": 75.0},
        ).get_json()
        self.assertEqual(payload["code"], 1010)

    def test_admin_reports_support_day_week_and_month_granularity(self):
        self._create_request(
            self.auth_headers,
            "2026-04-19T09:50:00",
            "FAST",
            20.0,
        )
        with self.app.app_context():
            run_normal_scheduler(event_time="2026-04-19T10:30:00", charge_mode="FAST")

        day_payload = self.client.get(
            "/api/admin/reports?granularity=day",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(day_payload["granularity"], "day")
        self.assertEqual(
            day_payload["rows"],
            [
                {
                    "time_key": "2026-04-19",
                    "station_code": "FAST_01",
                    "total_charge_count": 1,
                    "total_charge_seconds": 2400,
                    "total_charge_energy": 20.0,
                    "total_charge_fee": 18.5,
                    "total_service_fee": 16.0,
                    "total_fee": 34.5,
                }
            ],
        )

        week_payload = self.client.get(
            "/api/admin/reports?granularity=week",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(week_payload["rows"][0]["time_key"], "2026-W16")

        month_payload = self.client.get(
            "/api/admin/reports?granularity=month",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(month_payload["rows"][0]["time_key"], "2026-04")

    def test_admin_can_update_dispatch_mode(self):
        payload = self.client.put(
            "/api/admin/system/dispatch-mode",
            headers=self.admin_headers,
            json={"dispatch_mode": "EXT_SINGLE_BATCH"},
        ).get_json()["data"]
        self.assertEqual(payload, {"dispatch_mode": "EXT_SINGLE_BATCH"})

        config_payload = self.client.get(
            "/api/admin/system/config",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(config_payload["dispatch_mode"], "EXT_SINGLE_BATCH")

    def test_batch_simulate_ext_single_batch_optimizes_within_charge_mode(self):
        payload = self.client.post(
            "/api/test/batch-simulate",
            json={
                "test_case_id": "E-CASE-SINGLE",
                "scenario": {
                    "fast_station_count": 2,
                    "slow_station_count": 0,
                    "waiting_area_capacity": 6,
                    "charging_queue_len": 1,
                    "dispatch_mode": "EXT_SINGLE_BATCH",
                    "fault_dispatch_mode": "TIME_ORDER",
                },
                "users": [
                    {
                        "user_id": "U001",
                        "request_time": "2026-04-19T10:00:00",
                        "charge_mode": "FAST",
                        "request_energy": 30.0,
                    },
                    {
                        "user_id": "U002",
                        "request_time": "2026-04-19T10:00:00",
                        "charge_mode": "FAST",
                        "request_energy": 10.0,
                    },
                ],
            },
        ).get_json()["data"]

        self.assertEqual(payload["scenario"]["dispatch_mode"], "EXT_SINGLE_BATCH")
        self.assertEqual(payload["summary"]["total_users"], 2)
        self.assertEqual(payload["summary"]["completed_users"], 2)
        by_user = {item["user_id"]: item for item in payload["results"]}
        self.assertEqual(by_user["U001"]["detail"]["station_code"], "FAST_02")
        self.assertEqual(by_user["U002"]["detail"]["station_code"], "FAST_01")

    def test_batch_simulate_ext_full_batch_allows_cross_mode_assignment(self):
        payload = self.client.post(
            "/api/test/batch-simulate",
            json={
                "test_case_id": "E-CASE-FULL",
                "scenario": {
                    "fast_station_count": 1,
                    "slow_station_count": 1,
                    "waiting_area_capacity": 2,
                    "charging_queue_len": 1,
                    "dispatch_mode": "EXT_FULL_BATCH",
                    "fault_dispatch_mode": "TIME_ORDER",
                },
                "users": [
                    {
                        "user_id": "U001",
                        "request_time": "2026-04-19T10:00:00",
                        "charge_mode": "SLOW",
                        "request_energy": 30.0,
                    },
                    {
                        "user_id": "U002",
                        "request_time": "2026-04-19T10:00:00",
                        "charge_mode": "SLOW",
                        "request_energy": 10.0,
                    },
                ],
            },
        ).get_json()["data"]

        self.assertEqual(payload["scenario"]["dispatch_mode"], "EXT_FULL_BATCH")
        self.assertEqual(payload["summary"]["completed_users"], 2)
        by_user = {item["user_id"]: item for item in payload["results"]}
        self.assertEqual(by_user["U002"]["detail"]["station_code"], "FAST_01")
        self.assertEqual(by_user["U001"]["detail"]["station_code"], "SLOW_01")

    def test_batch_simulate_supports_fault_and_recover_events(self):
        payload = self.client.post(
            "/api/test/batch-simulate",
            json={
                "test_case_id": "F-CASE-BATCH",
                "scenario": {
                    "fast_station_count": 2,
                    "slow_station_count": 0,
                    "waiting_area_capacity": 6,
                    "charging_queue_len": 2,
                    "dispatch_mode": "NORMAL",
                    "fault_dispatch_mode": "TIME_ORDER",
                },
                "users": [
                    {
                        "user_id": "U001",
                        "request_time": "2026-04-19T10:00:00",
                        "charge_mode": "FAST",
                        "request_energy": 30.0,
                    },
                    {
                        "user_id": "U002",
                        "request_time": "2026-04-19T10:01:00",
                        "charge_mode": "FAST",
                        "request_energy": 30.0,
                    },
                    {
                        "user_id": "U003",
                        "request_time": "2026-04-19T10:02:00",
                        "charge_mode": "FAST",
                        "request_energy": 30.0,
                    },
                ],
                "events": [
                    {"at": "2026-04-19T10:20:00", "type": "FAULT", "station_code": "FAST_01"},
                    {"at": "2026-04-19T10:50:00", "type": "RECOVER", "station_code": "FAST_01"},
                ],
            },
        ).get_json()["data"]

        self.assertEqual(payload["scenario"]["fault_dispatch_mode"], "TIME_ORDER")
        self.assertEqual(len(payload["events_result"]), 2)
        self.assertEqual(payload["events_result"][0]["type"], "FAULT")
        self.assertEqual(payload["events_result"][0]["station_code"], "FAST_01")
        self.assertEqual(payload["events_result"][0]["result"]["interrupted_request_id"], "REQ0001")
        self.assertEqual(payload["events_result"][0]["result"]["remaining_request_id"], "REQ0004")
        self.assertEqual(payload["events_result"][1]["type"], "RECOVER")
        self.assertEqual(payload["summary"]["total_users"], 3)
        self.assertEqual(payload["summary"]["completed_users"], 3)
        by_user = {item["user_id"]: item for item in payload["results"]}
        self.assertEqual(by_user["U001"]["final_status"], "FAULT_INTERRUPTED")
        self.assertEqual(by_user["U001"]["detail"]["request_status"], "FAULT_INTERRUPTED")
        self.assertEqual(by_user["U001"]["detail"]["actual_energy"], 10.0)
        self.assertEqual(by_user["U001"]["followup_request_id"], "REQ0004")
        self.assertEqual(by_user["U001"]["followup_request_ids"], ["REQ0004"])
        self.assertIn(by_user["U003"]["final_status"], {"COMPLETED", "CHARGING", "QUEUED"})

    def test_batch_simulate_enforces_waiting_area_capacity_for_same_time_arrivals(self):
        payload = self.client.post(
            "/api/test/batch-simulate",
            json={
                "test_case_id": "CAPACITY_LIMIT",
                "scenario": {
                    "fast_station_count": 1,
                    "slow_station_count": 0,
                    "waiting_area_capacity": 1,
                    "charging_queue_len": 1,
                    "dispatch_mode": "NORMAL",
                    "fault_dispatch_mode": "TIME_ORDER",
                },
                "users": [
                    {
                        "user_id": "U001",
                        "request_time": "2026-04-19T10:00:00",
                        "charge_mode": "FAST",
                        "request_energy": 20.0,
                    },
                    {
                        "user_id": "U002",
                        "request_time": "2026-04-19T10:00:00",
                        "charge_mode": "FAST",
                        "request_energy": 20.0,
                    },
                ],
            },
        ).get_json()["data"]

        self.assertEqual(payload["scenario"]["waiting_area_capacity"], 1)
        self.assertEqual(payload["summary"]["total_users"], 2)
        self.assertEqual(payload["summary"]["completed_users"], 1)
        self.assertEqual(payload["summary"]["rejected_users"], 1)
        by_user = {item["user_id"]: item for item in payload["results"]}
        self.assertEqual(by_user["U001"]["final_status"], "COMPLETED")
        self.assertTrue(by_user["U001"]["accepted"])
        self.assertEqual(by_user["U002"]["final_status"], "REJECTED_WAITING_AREA_FULL")
        self.assertFalse(by_user["U002"]["accepted"])
        self.assertEqual(by_user["U002"]["reject_reason"], "WAITING_AREA_FULL")
        self.assertIsNone(by_user["U002"]["request_id"])
        self.assertIsNone(by_user["U002"]["queue_number"])
        self.assertIsNone(by_user["U002"]["detail"])

        with self.app.app_context():
            row = query_db(
                """
                SELECT COUNT(*) AS cnt
                FROM charge_request
                WHERE request_id IS NOT NULL
                """,
                one=True,
        )
        self.assertEqual(int(row["cnt"]), 1)

    def test_batch_simulate_accepts_station_queue_capacity_alias(self):
        payload = self.client.post(
            "/api/test/batch-simulate",
            json={
                "test_case_id": "ALIAS-STATION-QUEUE",
                "scenario": {
                    "fast_station_count": 1,
                    "slow_station_count": 1,
                    "waiting_area_capacity": 2,
                    "station_queue_capacity": 1,
                    "dispatch_mode": "NORMAL",
                    "fault_dispatch_mode": "TIME_ORDER",
                },
                "users": [
                    {
                        "user_id": "U001",
                        "request_time": "2026-04-19T10:00:00",
                        "charge_mode": "FAST",
                        "request_energy": 20.0,
                    }
                ],
            },
        ).get_json()["data"]

        self.assertEqual(payload["scenario"]["charging_queue_len"], 1)
        self.assertNotIn("station_queue_capacity", payload["scenario"])
        self.assertEqual(payload["summary"]["total_users"], 1)
        self.assertEqual(payload["summary"]["completed_users"], 1)
        self.assertTrue(payload["results"][0]["accepted"])

    def test_batch_simulate_updates_admin_visible_waiting_area_capacity(self):
        self.client.post(
            "/api/test/batch-simulate",
            json={
                "test_case_id": "CONFIG-SYNC",
                "scenario": {
                    "fast_station_count": 1,
                    "slow_station_count": 1,
                    "waiting_area_capacity": 1,
                    "charging_queue_len": 3,
                    "dispatch_mode": "EXT_SINGLE_BATCH",
                    "fault_dispatch_mode": "PRIORITY",
                },
                "users": [],
            },
        )

        self.client.post(
            "/api/auth/register",
            json={
                "username": "admin_batch",
                "password": "secret12",
                "battery_capacity": 80.0,
                "role": "ADMIN",
            },
        )
        admin_login = self.client.post(
            "/api/auth/login",
            json={"username": "admin_batch", "password": "secret12"},
        ).get_json()
        admin_headers = {"Authorization": f"Bearer {admin_login['data']['token']}"}

        payload = self.client.get(
            "/api/admin/system/config",
            headers=admin_headers,
        ).get_json()["data"]
        self.assertEqual(payload["fast_station_count"], 1)
        self.assertEqual(payload["slow_station_count"], 1)
        self.assertEqual(payload["waiting_area_capacity"], 1)
        self.assertEqual(payload["charging_queue_len"], 3)
        self.assertEqual(payload["dispatch_mode"], "EXT_SINGLE_BATCH")
        self.assertEqual(payload["fault_dispatch_mode"], "PRIORITY")

    def test_admin_system_config_returns_v3_fields(self):
        payload = self.client.get(
            "/api/admin/system/config",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(
            payload,
            {
                "fast_station_count": 3,
                "slow_station_count": 2,
                "waiting_area_capacity": 6,
                "charging_queue_len": 2,
                "dispatch_mode": "NORMAL",
                "fault_dispatch_mode": "TIME_ORDER",
            },
        )

    def test_admin_stations_returns_v3_station_snapshot(self):
        user2_headers = self._register_and_login("user_002")
        user3_headers = self._register_and_login("user_003")
        user4_headers = self._register_and_login("user_004")

        req1 = self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)["data"]["request_id"]
        self._create_request(user2_headers, "2026-04-19T10:01:00", "FAST", 20.0)
        self._create_request(user3_headers, "2026-04-19T10:02:00", "FAST", 20.0)
        self._create_request(user4_headers, "2026-04-19T10:03:00", "FAST", 10.0)

        payload = self.client.get(
            "/api/admin/stations",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(len(payload), 5)
        fast1 = next(item for item in payload if item["station_code"] == "FAST_01")
        self.assertEqual(
            set(fast1.keys()),
            {
                "station_code",
                "charge_mode",
                "station_status",
                "current_request_id",
                "queue_length",
                "total_charge_count",
                "total_charge_seconds",
                "total_charge_energy",
            },
        )
        self.assertEqual(fast1["charge_mode"], "FAST")
        self.assertEqual(fast1["station_status"], "RUNNING")
        self.assertEqual(fast1["current_request_id"], req1)
        self.assertEqual(fast1["queue_length"], 2)
        self.assertEqual(fast1["total_charge_count"], 0)
        self.assertEqual(fast1["total_charge_seconds"], 0)
        self.assertEqual(fast1["total_charge_energy"], 0.0)

    def test_admin_station_queue_returns_fixed_queue_entries(self):
        user2_headers = self._register_and_login("user_002")
        user3_headers = self._register_and_login("user_003")
        user4_headers = self._register_and_login("user_004")

        self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)
        self._create_request(user2_headers, "2026-04-19T10:01:00", "FAST", 20.0)
        self._create_request(user3_headers, "2026-04-19T10:02:00", "FAST", 20.0)
        self._create_request(user4_headers, "2026-04-19T10:03:00", "FAST", 10.0)

        payload = self.client.get(
            "/api/admin/stations/FAST_01/queue",
            headers=self.admin_headers,
        ).get_json()["data"]
        self.assertEqual(payload["station_code"], "FAST_01")
        self.assertEqual(len(payload["queue"]), 2)
        self.assertEqual(
            payload["queue"][0],
            {
                "user_id": "U001",
                "battery_capacity": 60.0,
                "request_energy": 20.0,
                "queue_number": "F1",
                "queue_wait_seconds": 0,
            },
        )
        self.assertEqual(
            payload["queue"][1],
            {
                "user_id": "U005",
                "battery_capacity": 60.0,
                "request_energy": 10.0,
                "queue_number": "F4",
                "queue_wait_seconds": 2220,
            },
        )

    def test_legacy_stations_overview_uses_v3_schema_without_crashing(self):
        self._create_request(self.auth_headers, "2026-04-19T10:00:00", "FAST", 20.0)

        payload = self.client.get("/api/stations/overview").get_json()["data"]
        self.assertTrue(payload["deprecated"])
        self.assertEqual(payload["replacement"], "/api/admin/stations")
        self.assertEqual(len(payload["fast_stations"]), 3)
        self.assertEqual(len(payload["slow_stations"]), 2)

        fast1 = next(item for item in payload["fast_stations"] if item["station_code"] == "FAST_01")
        self.assertEqual(
            set(fast1.keys()),
            {
                "station_code",
                "charge_mode",
                "power_kw",
                "station_status",
                "current_request_id",
                "queue_length",
                "queue_capacity",
                "available_time",
                "total_charge_count",
                "total_charge_seconds",
                "total_charge_energy",
            },
        )
        self.assertEqual(fast1["charge_mode"], "FAST")
        self.assertEqual(fast1["station_status"], "RUNNING")
        self.assertEqual(fast1["current_request_id"], "REQ0001")
        self.assertEqual(payload["waiting_queue"]["capacity"], 6)
        self.assertEqual(payload["waiting_queue"]["total_waiting"], 0)

    def test_legacy_stations_overview_uses_batch_waiting_area_capacity(self):
        self.client.post(
            "/api/test/batch-simulate",
            json={
                "test_case_id": "LEGACY-OVERVIEW-CAPACITY",
                "scenario": {
                    "fast_station_count": 1,
                    "slow_station_count": 1,
                    "waiting_area_capacity": 1,
                    "charging_queue_len": 2,
                    "dispatch_mode": "NORMAL",
                    "fault_dispatch_mode": "TIME_ORDER",
                },
                "users": [],
            },
        )

        payload = self.client.get("/api/stations/overview").get_json()["data"]
        self.assertTrue(payload["deprecated"])
        self.assertEqual(payload["replacement"], "/api/admin/stations")
        self.assertEqual(payload["waiting_queue"]["capacity"], 1)
        self.assertEqual(len(payload["fast_stations"]), 1)
        self.assertEqual(len(payload["slow_stations"]), 1)

    def test_admin_routes_require_admin_role(self):
        response = self.client.get(
            "/api/admin/system/config",
            headers=self.auth_headers,
        ).get_json()
        self.assertEqual(response["code"], 1003)


if __name__ == "__main__":
    unittest.main()
