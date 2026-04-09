"""
最小鉴权回归测试
"""

import os
import sys
import tempfile
import unittest

from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.routes.auth import auth_bp
from app.utils.db import init_db


class MinimalAuthTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["DATABASE_PATH"] = self.db_path
        self.app.config["SECRET_KEY"] = "test-secret"
        self.app.config["JWT_EXPIRATION_HOURS"] = 24
        self.app.register_blueprint(auth_bp, url_prefix="/api/auth")
        init_db(self.app)
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_register_login_profile(self):
        register_resp = self.client.post(
            "/api/auth/register",
            json={"username": "user_001", "password": "secret12", "role": "USER"},
        ).get_json()
        self.assertEqual(register_resp["code"], 0)

        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "user_001", "password": "secret12"},
        ).get_json()
        self.assertEqual(login_resp["code"], 0)
        token = login_resp["data"]["token"]

        profile_resp = self.client.get(
            "/api/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
        ).get_json()
        self.assertEqual(profile_resp["code"], 0)
        self.assertEqual(profile_resp["data"]["username"], "user_001")


if __name__ == "__main__":
    unittest.main()
