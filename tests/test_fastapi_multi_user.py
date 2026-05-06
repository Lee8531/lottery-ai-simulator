from contextlib import contextmanager
from contextlib import redirect_stdout
import io
import os
import shutil
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from lottery_sim.fastapi_app import create_fastapi_app, _render_login_page


@contextmanager
def _temp_dir():
    base = Path(os.environ.get("TEST_TMPDIR", Path.cwd() / ".test-tmp"))
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"fastapi-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


class FastApiMultiUserTests(unittest.TestCase):
    def make_client(self, root: Path) -> TestClient:
        env = {
            "LOTTERY_ADMIN_USER": "admin",
            "LOTTERY_ADMIN_PASSWORD": "secret",
        }
        patcher = patch.dict(os.environ, env, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        app = create_fastapi_app(root / "reports" / "latest", root)
        return TestClient(app)

    def login(self, client: TestClient):
        return client.post(
            "/login",
            data={"username": "admin", "password": "secret"},
            follow_redirects=False,
        )

    def test_unauthenticated_dashboard_redirects_to_login(self):
        with _temp_dir() as tmp:
            client = self.make_client(Path(tmp))

            response = client.get("/", follow_redirects=False)

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/login")

    def test_unauthenticated_api_returns_401(self):
        with _temp_dir() as tmp:
            client = self.make_client(Path(tmp))

            response = client.post("/api/jobs/daily?game=ssq")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "authentication required")

    def test_login_sets_session_cookie(self):
        with _temp_dir() as tmp:
            client = self.make_client(Path(tmp))

            response = self.login(client)

        self.assertEqual(response.status_code, 303)
        self.assertIn("lottery_session=", response.headers["set-cookie"])

    def test_login_page_uses_polished_chinese_layout(self):
        page = _render_login_page()

        self.assertIn("彩票模拟分析系统", page)
        self.assertIn("账号登录", page)
        self.assertIn('class="login-shell"', page)
        self.assertIn('class="register-link"', page)
        self.assertIn('href="/register"', page)
        self.assertNotIn("admin / admin", page)
        self.assertNotIn("LOTTERY_ADMIN_PASSWORD", page)
        self.assertNotIn("<h1>Login</h1>", page)

    def test_registration_page_is_available_without_default_password_notice(self):
        with _temp_dir() as tmp:
            client = self.make_client(Path(tmp))

            response = client.get("/register")

        self.assertEqual(response.status_code, 200)
        self.assertIn('action="/register"', response.text)
        self.assertIn('name="username"', response.text)
        self.assertIn('name="password"', response.text)
        self.assertNotIn("admin / admin", response.text)
        self.assertNotIn("LOTTERY_ADMIN_PASSWORD", response.text)

    def test_default_admin_password_is_not_printed_when_bootstrapping(self):
        with _temp_dir() as tmp:
            env = {
                key: value
                for key, value in os.environ.items()
                if key not in {"LOTTERY_ADMIN_USER", "LOTTERY_ADMIN_PASSWORD"}
            }
            output = io.StringIO()

            with patch.dict(os.environ, env, clear=True), redirect_stdout(output):
                create_fastapi_app(Path(tmp) / "reports" / "latest", Path(tmp))

        self.assertNotIn("admin/admin", output.getvalue())
        self.assertNotIn("LOTTERY_ADMIN_PASSWORD", output.getvalue())

    def test_registration_creates_user_session_and_user_workspace(self):
        with _temp_dir() as tmp:
            root = Path(tmp)
            client = self.make_client(root)
            register_response = client.post(
                "/register",
                data={"username": "alice", "password": "secret123"},
                follow_redirects=False,
            )
            seen = {}

            def load_model(path):
                seen["reports_dir"] = Path(path)
                return object()

            with (
                patch("lottery_sim.fastapi_app.load_dashboard_model", side_effect=load_model),
                patch("lottery_sim.fastapi_app.render_dashboard_html", return_value="<html><body></body></html>"),
            ):
                dashboard_response = client.get("/")

        self.assertEqual(register_response.status_code, 303)
        self.assertEqual(register_response.headers["location"], "/")
        self.assertIn("lottery_session=", register_response.headers["set-cookie"])
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(seen["reports_dir"], root / "reports" / "users" / "alice" / "latest")

    def test_duplicate_registration_returns_conflict(self):
        with _temp_dir() as tmp:
            client = self.make_client(Path(tmp))

            first = client.post(
                "/register",
                data={"username": "alice", "password": "secret123"},
                follow_redirects=False,
            )
            second = client.post(
                "/register",
                data={"username": "alice", "password": "other-secret"},
                follow_redirects=False,
            )

        self.assertEqual(first.status_code, 303)
        self.assertEqual(second.status_code, 409)

    def test_authenticated_dashboard_uses_current_user_report_directory(self):
        with _temp_dir() as tmp:
            root = Path(tmp)
            client = self.make_client(root)
            self.login(client)
            seen = {}

            def load_model(path):
                seen["reports_dir"] = Path(path)
                return object()

            with (
                patch("lottery_sim.fastapi_app.load_dashboard_model", side_effect=load_model),
                patch("lottery_sim.fastapi_app.render_dashboard_html", return_value="<html><body></body></html>"),
            ):
                response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(seen["reports_dir"], root / "reports" / "users" / "admin" / "latest")

    def test_job_start_uses_current_user_workspace_paths(self):
        with _temp_dir() as tmp:
            root = Path(tmp)
            client = self.make_client(root)
            self.login(client)
            seen = {}

            def start_job(action, repo_root, **kwargs):
                seen["action"] = action
                seen["repo_root"] = Path(repo_root)
                seen.update(kwargs)
                return SimpleNamespace(status="running")

            with (
                patch("lottery_sim.fastapi_app.start_dashboard_job", side_effect=start_job),
                patch("lottery_sim.fastapi_app._job_snapshot", return_value={"status": "running"}),
            ):
                response = client.post("/api/jobs/daily?game=ssq")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(seen["action"], "daily")
        self.assertEqual(seen["repo_root"], root)
        self.assertEqual(seen["game_code"], "ssq")
        self.assertEqual(seen["user_key"], "admin")
        self.assertEqual(seen["data_dir"], root / "data" / "normalized")
        self.assertEqual(seen["report_dir"], root / "reports" / "users" / "admin" / "latest")
        self.assertEqual(seen["recommendation_dir"], root / "data" / "users" / "admin" / "recommendations")
        self.assertEqual(seen["model_dir"], root / "data" / "users" / "admin" / "models")
        self.assertEqual(seen["history_data_dir"], root / "data" / "users" / "admin")


if __name__ == "__main__":
    unittest.main()
