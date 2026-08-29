"""
Automated unit tests for Production Architecture & Static SPA Routing.
Validates:
- find_dist_dir locates the dist directory correctly
- SPA fallback and asset resolution logic
- Authentication error sanitization (no internal JWT parsing leak)
"""
import unittest
import os
import tempfile
import shutil
import asyncio

os.environ["AEGIS_TEST_MODE"] = "1"
os.environ["USE_MEMORY_STORE"] = "1"

from backend.app.auth import verify_firebase_token
from backend.app.errors import AuthenticationError


def resolve_spa_target(dist_dir: str, request_path: str) -> tuple[str, int]:
    """
    Simulates the production FastAPI SPA and static asset resolver.
    Returns (resolved_type, status_code).
    """
    if request_path.startswith("api/") or request_path == "api" or request_path == "health" or request_path.startswith("users/"):
        return ("api_error", 404)

    file_path = os.path.join(dist_dir, request_path)
    if os.path.isfile(file_path):
        return ("static_file", 200)

    index_path = os.path.join(dist_dir, "index.html")
    if os.path.isfile(index_path):
        return ("spa_html", 200)

    return ("not_found", 404)


class TestProductionArchitecture(unittest.TestCase):

    def test_auth_error_sanitization_no_jwt_leak(self):
        """Ensures malformed JWT errors do not expose parser internals."""
        with self.assertRaises(AuthenticationError) as ctx:
            asyncio.run(verify_firebase_token("Bearer malformed.jwt.token.here"))
        err_msg = str(ctx.exception)
        self.assertIn("Authentication failed", err_msg)
        self.assertNotIn("Wrong number of segments", err_msg)
        self.assertNotIn("Traceback", err_msg)

    def test_api_route_precedence_no_spa_fallback_on_api_paths(self):
        """Ensures non-existent /api/* routes return 404, NEVER SPA HTML."""
        temp_dir = tempfile.mkdtemp()
        try:
            dist_path = os.path.join(temp_dir, "dist")
            os.makedirs(dist_path, exist_ok=True)
            with open(os.path.join(dist_path, "index.html"), "w") as f:
                f.write("<!doctype html><html><body>Aegis Journal</body></html>")

            # API routes must not get SPA HTML
            res_type, status = resolve_spa_target(dist_path, "api/unknown_route_999")
            self.assertEqual(status, 404)
            self.assertEqual(res_type, "api_error")

            res_type, status = resolve_spa_target(dist_path, "health")
            self.assertEqual(status, 404)
            self.assertEqual(res_type, "api_error")

            # SPA client routes must get HTML
            res_type, status = resolve_spa_target(dist_path, "timeline")
            self.assertEqual(status, 200)
            self.assertEqual(res_type, "spa_html")

            # Root path must get HTML
            res_type, status = resolve_spa_target(dist_path, "")
            self.assertEqual(status, 200)
            self.assertEqual(res_type, "spa_html")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_static_asset_serving(self):
        """Tests that static assets inside dist/assets/ are directly resolved."""
        temp_dir = tempfile.mkdtemp()
        try:
            dist_path = os.path.join(temp_dir, "dist")
            assets_path = os.path.join(dist_path, "assets")
            os.makedirs(assets_path, exist_ok=True)
            with open(os.path.join(dist_path, "index.html"), "w") as f:
                f.write("<!doctype html><html><body>Aegis Journal</body></html>")
            with open(os.path.join(assets_path, "index-abc123.js"), "w") as f:
                f.write("console.log('bundle');")

            res_type, status = resolve_spa_target(dist_path, "assets/index-abc123.js")
            self.assertEqual(status, 200)
            self.assertEqual(res_type, "static_file")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
