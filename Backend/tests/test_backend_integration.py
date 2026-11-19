import sys
import time
import unittest
from pathlib import Path

# Setup sys.path
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
ML_DIR = PROJECT_ROOT / "ML"

for p in [str(BACKEND_DIR), str(PROJECT_ROOT), str(ML_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from app.main import app


class TestBackendIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_email = f"audit_user_{int(time.time())}@kiit.ac.in"
        cls.test_password = "SecurePassword123!"
        cls.token = None

    def test_01_health_check(self):
        """GET /health should return 200 healthy status."""
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("status"), "healthy")

    def test_02_register_user(self):
        """POST /auth/register should create a new user account."""
        r = self.client.post("/auth/register", json={
            "full_name": "Integration Test User",
            "email": self.test_email,
            "password": self.test_password,
            "phone_number": "+919876543210"
        })
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["email"], self.test_email)
        self.assertEqual(data["full_name"], "Integration Test User")

    def test_03_login_success(self):
        """POST /auth/login should authenticate user and issue a valid JWT access token."""
        r = self.client.post("/auth/login", data={
            "username": self.test_email,
            "password": self.test_password
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("access_token", data)
        self.assertEqual(data.get("token_type"), "bearer")
        TestBackendIntegration.token = data["access_token"]

    def test_04_login_invalid_password(self):
        """POST /auth/login with wrong password should return 401."""
        r = self.client.post("/auth/login", data={
            "username": self.test_email,
            "password": "WrongPassword!"
        })
        self.assertEqual(r.status_code, 401)
        self.assertIn("Invalid email or password", r.json().get("detail", ""))

    def test_05_protected_route_with_token(self):
        """GET /protected should authorize access using the bearer token."""
        self.assertIsNotNone(self.token)
        r = self.client.get("/protected", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("message"), "You are authenticated!")

    def test_06_user_profile_me(self):
        """GET /users/me should return the authenticated user's profile."""
        self.assertIsNotNone(self.token)
        r = self.client.get("/users/me", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["email"], self.test_email)

    def test_07_invalid_token_rejected(self):
        """Protected endpoint with an invalid token should return 401."""
        r = self.client.get("/users/me", headers={
            "Authorization": "Bearer invalid_tampered_token"
        })
        self.assertEqual(r.status_code, 401)

    def test_08_safe_route_calculation_with_geometry(self):
        """POST /routes/safe-route should calculate a road route preserving geometry."""
        payload = {
            "source_latitude": 20.3545,
            "source_longitude": 85.8161,
            "destination_latitude": 20.3590,
            "destination_longitude": 85.8210,
            "mode": "safest"
        }
        r = self.client.post("/routes/safe-route", json=payload)
        self.assertEqual(r.status_code, 200)
        data = r.json()

        self.assertGreater(data["total_distance_m"], 0.0)
        self.assertGreater(len(data["path_coordinates"]), 2)
        self.assertGreater(len(data["segments"]), 0)

        # Check geometry preservation on segments
        first_seg = data["segments"][0]
        self.assertIn("geometry", first_seg)
        self.assertIsInstance(first_seg["geometry"], list)
        self.assertGreaterEqual(len(first_seg["geometry"]), 2)

        # Check honest XAI reporting
        self.assertIn("xai_contributing_factors", data)
        self.assertIsInstance(data["xai_contributing_factors"], list)

    def test_09_route_comparison(self):
        """POST /routes/compare should evaluate Safest, Balanced, and Fastest routes."""
        payload = {
            "source_latitude": 20.3545,
            "source_longitude": 85.8161,
            "destination_latitude": 20.3590,
            "destination_longitude": 85.8210
        }
        r = self.client.post("/routes/compare", json=payload)
        self.assertEqual(r.status_code, 200)
        data = r.json()

        self.assertIn("routes", data)
        self.assertEqual(len(data["routes"]), 3)

        modes = [rt["mode"] for rt in data["routes"]]
        self.assertIn("safest", modes)
        self.assertIn("balanced", modes)
        self.assertIn("fastest", modes)

        # Check that recommended route is Safest
        safest_route = next(rt for rt in data["routes"] if rt["mode"] == "safest")
        self.assertTrue(safest_route["recommended"])

    def test_10_deviation_monitoring(self):
        """POST /routes/deviation should detect when user wanders off planned path."""
        planned = [
            [20.3545, 85.8161],
            [20.3550, 85.8170],
            [20.3560, 85.8180]
        ]
        # On-route coordinates
        r_on = self.client.post("/routes/deviation", json={
            "current_latitude": 20.3546,
            "current_longitude": 85.8162,
            "planned_path": planned,
            "threshold_meters": 100.0
        })
        self.assertEqual(r_on.status_code, 200)
        self.assertFalse(r_on.json()["deviated"])

        # Off-route coordinates (~400m away)
        r_off = self.client.post("/routes/deviation", json={
            "current_latitude": 20.3600,
            "current_longitude": 85.8161,
            "planned_path": planned,
            "threshold_meters": 100.0
        })
        self.assertEqual(r_off.status_code, 200)
        self.assertTrue(r_off.json()["deviated"])
        self.assertIn("warning_message", r_off.json())

    def test_11_invalid_coordinates_validation(self):
        """Out-of-range coordinates should be rejected with 422."""
        r = self.client.post("/routes/safe-route", json={
            "source_latitude": 120.0,  # Invalid latitude > 90
            "source_longitude": 85.8161,
            "destination_latitude": 20.3590,
            "destination_longitude": 85.8210
        })
        self.assertEqual(r.status_code, 422)

    def test_12_route_comparison_kiit_to_bhubaneswar_station(self):
        """POST /routes/compare from KIIT to Bhubaneswar Station must return all 3 routes."""
        payload = {
            "source_latitude": 20.354563,
            "source_longitude": 85.816109,
            "destination_latitude": 20.2667774,
            "destination_longitude": 85.8435592
        }
        r = self.client.post("/routes/compare", json=payload)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("routes", data)
        self.assertEqual(len(data["routes"]), 3)

        modes = [rt["mode"] for rt in data["routes"]]
        self.assertEqual(modes, ["safest", "balanced", "fastest"])

        for rt in data["routes"]:
            self.assertGreater(len(rt["path_coordinates"]), 0)
            self.assertGreater(len(rt["segments"]), 0)
            for seg in rt["segments"]:
                self.assertIn("geometry", seg)
                self.assertGreaterEqual(len(seg["geometry"]), 2)



if __name__ == "__main__":
    unittest.main()
