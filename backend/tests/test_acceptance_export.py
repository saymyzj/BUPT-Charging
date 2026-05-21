"""Acceptance console xlsx export regression tests."""

import os
import sys
import tempfile
import unittest

from flask import Flask
from openpyxl import load_workbook

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.acceptance_service import (
    DEFAULT_START_TIME,
    build_snapshot,
    execute_event,
    export_table_xlsx,
    replace_events,
    reset_acceptance,
    save_snapshot,
)
from app.utils.db import init_db


class AcceptanceExportTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.log_dir = tempfile.mkdtemp()
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            DATABASE_PATH=self.db_path,
            LOG_DIR=self.log_dir,
            SECRET_KEY="test-secret",
            JWT_EXPIRATION_HOURS=24,
            AUTO_REBUILD_INCOMPATIBLE_DB=True,
            FAST_CHARGING_PILE_NUM=3,
            TRICKLE_CHARGING_PILE_NUM=2,
            CHARGING_QUEUE_LEN=3,
            WAITING_AREA_SIZE=10,
            DISPATCH_MODE="NORMAL",
            FAULT_DISPATCH_MODE="PRIORITY",
        )
        self.ctx = self.app.app_context()
        self.ctx.push()
        init_db(self.app)

    def tearDown(self):
        self.ctx.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_export_uses_table_view_columns(self):
        reset_acceptance("sample.xlsx")
        replace_events(
            [
                {
                    "event_id": "EVT0001",
                    "source": "XLSX",
                    "at": DEFAULT_START_TIME,
                    "event_type": "APPLY",
                    "vehicle_code": "V1",
                    "charge_mode": "FAST",
                    "value": 20,
                    "raw_text": "(A,V1,F,20)",
                    "enabled": True,
                }
            ],
            "sample.xlsx",
        )
        snapshot = build_snapshot(DEFAULT_START_TIME, phase="AFTER")
        save_snapshot("EVT0001", DEFAULT_START_TIME, "AFTER", snapshot)

        workbook = load_workbook(export_table_xlsx(), data_only=True)
        sheet = workbook.active

        self.assertEqual(sheet.title, "表格视图")
        self.assertEqual(sheet.max_column, 8)
        self.assertEqual(sheet.cell(1, 3).value, "(车号,已充电量,当前费用)")
        self.assertEqual(sheet.cell(1, 8).value, "等候区(车号,充电类型,充电量)；故障队列(车号,已充电量,当前费用)")
        self.assertEqual(
            [sheet.cell(2, column).value for column in range(1, 9)],
            ["时刻", "事件", "快充1", "快充2", "快充3", "慢充1", "慢充2", "等候区"],
        )
        self.assertEqual(sheet.cell(3, 1).value, "06:00:00")
        self.assertEqual(sheet.cell(3, 2).value, "(A,V1,F,20)")

    def test_export_uses_tuple_cells_for_station_queues(self):
        reset_acceptance("sample.xlsx")
        replace_events(
            [
                {
                    "event_id": "EVT0001",
                    "source": "XLSX",
                    "at": DEFAULT_START_TIME,
                    "event_type": "APPLY",
                    "vehicle_code": "V1",
                    "charge_mode": "FAST",
                    "value": 20,
                    "raw_text": "(A,V1,F,20)",
                    "enabled": True,
                }
            ],
            "sample.xlsx",
        )
        execute_event("EVT0001")

        workbook = load_workbook(export_table_xlsx(), data_only=True)
        sheet = workbook.active

        self.assertEqual(sheet.cell(3, 3).value, "(V1,0,0)")
        self.assertNotIn("充电中", sheet.cell(3, 3).value)
        self.assertNotIn("费用", sheet.cell(3, 3).value)


if __name__ == "__main__":
    unittest.main()
