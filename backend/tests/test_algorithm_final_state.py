"""Legacy V2 调度测试，Day 3 暂不纳入运行。"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

raise unittest.SkipTest("Legacy V2 scheduler test; superseded by V3 Day 3 minimal closure.")

from app.services.scheduler_engine import handle_station_fault
from app.utils.db import execute_db, init_db, query_db


class AlgorithmFinalStateTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["DATABASE_PATH"] = self.db_path
        init_db(self.app)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_fault_creates_new_followup_request_and_keeps_original_record(self):
        with self.app.app_context():
            submit_time = "2026-04-10T10:00:00"
            start_time = datetime(2026, 4, 10, 10, 5, 0)
            fault_time = start_time + timedelta(minutes=10)
            estimated_finish = start_time + timedelta(minutes=40)

            execute_db(
                """
                INSERT INTO charge_request (
                    request_id, charge_mode, request_energy, remaining_energy, battery_limit_energy,
                    status, waiting_pool_type, scenario_id, submit_time,
                    estimated_start_time, estimated_finish_time, estimated_service_seconds,
                    assigned_station_id, confirmed_at
                ) VALUES (?, 'FAST', 20.0, 20.0, 20.0, 'CHARGING', 'FAST_POOL', 1, ?, ?, ?, ?, 1, ?)
                """,
                [
                    "REQ900",
                    submit_time,
                    start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    estimated_finish.strftime("%Y-%m-%dT%H:%M:%S"),
                    2400,
                    start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                ],
            )
            request_row = query_db("SELECT id FROM charge_request WHERE request_id = 'REQ900'", one=True)
            execute_db(
                """
                UPDATE charging_station
                SET status = 'CHARGING', current_request_id = ?, available_time = ?
                WHERE id = 1
                """,
                [
                    request_row["id"],
                    estimated_finish.strftime("%Y-%m-%dT%H:%M:%S"),
                ],
            )
            execute_db(
                """
                INSERT INTO charging_session (
                    request_id, station_id, start_time, status, actual_energy
                ) VALUES (?, 1, ?, 'CHARGING', 0.0)
                """,
                [
                    request_row["id"],
                    start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                ],
            )

            result = handle_station_fault(1, event_time=fault_time)
            self.assertTrue(result["success"])
            self.assertEqual(result["original_request_id"], "REQ900")
            self.assertIsNotNone(result["followup_request_id"])

            original = query_db("SELECT * FROM charge_request WHERE request_id = 'REQ900'", one=True)
            self.assertEqual(original["status"], "INTERRUPTED")
            self.assertGreater(original["actual_energy"], 0.0)

            followup = query_db(
                "SELECT * FROM charge_request WHERE request_id = ?",
                [result["followup_request_id"]],
                one=True,
            )
            self.assertIsNotNone(followup)
            self.assertEqual(followup["status"], "WAITING")
            self.assertEqual(followup["fault_requeue_flag"], 1)
            self.assertLess(float(followup["request_energy"]), 20.0)

            station = query_db("SELECT status FROM charging_station WHERE id = 1", one=True)
            self.assertEqual(station["status"], "FAULT")


if __name__ == "__main__":
    unittest.main()
