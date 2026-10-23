"""Offline SQLite and API tests using temporary databases."""

from io import BytesIO
from pathlib import Path
import sqlite3
import tempfile
import unittest
from contextlib import closing

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.api.generate import router as generate_router
from app.api.history import router as history_router
from app.services.history_service import HistoryRepository


class FakeBlip:
    def generate_caption(self, image):
        return "A mountain lake"


class FakeGroq:
    def generate_caption(self, **kwargs):
        return "Explore the quiet mountain lake."


class FailingGroq:
    def generate_caption(self, **kwargs):
        raise RuntimeError("provider unavailable")


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "nested" / "test_history.db"
        self.repository = HistoryRepository(self.database_path)
        self.repository.initialize()
        self.app = FastAPI()
        self.app.state.history_repository = self.repository
        self.app.include_router(history_router, prefix="/api/v1")
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.temp_dir.cleanup()

    def insert(self, caption: str, template: str | None = None):
        return self.repository.insert(
            base_caption=f"Base {caption}",
            generated_caption=f"Generated {caption}",
            platform="Instagram",
            language="English",
            writing_style="Creative",
            visual_template=template,
        )

    def test_initialization_insertion_and_persistence_across_connections(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'caption_history'"
            ).fetchone()
        self.assertIsNotNone(table)
        created = self.insert("one", "instagram_creative")
        another_connection = HistoryRepository(self.database_path)
        self.assertEqual(another_connection.get(created["id"])["generated_caption"], "Generated one")
        self.assertTrue(created["created_at_utc"].endswith("Z"))

    def test_list_order_and_pagination(self):
        first = self.insert("one")
        second = self.insert("two")
        third = self.insert("three")
        response = self.client.get("/api/v1/history/", params={"limit": 2, "offset": 0})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 3)
        self.assertEqual([row["id"] for row in payload["records"]], [third["id"], second["id"]])
        page = self.client.get("/api/v1/history/", params={"limit": 2, "offset": 2}).json()
        self.assertEqual([row["id"] for row in page["records"]], [first["id"]])
        self.assertEqual(self.client.get("/api/v1/history/?limit=0").status_code, 422)

    def test_get_delete_and_not_found(self):
        row = self.insert("lookup")
        result = self.client.get(f"/api/v1/history/{row['id']}")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["base_caption"], "Base lookup")
        self.assertEqual(self.client.get("/api/v1/history/9999").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/v1/history/{row['id']}").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/v1/history/{row['id']}").status_code, 404)

    def test_combined_generation_records_only_successful_caption_pairs(self):
        app = FastAPI()
        app.state.history_repository = self.repository
        app.state.blip_service = FakeBlip()
        app.state.groq_service = FakeGroq()
        app.include_router(generate_router, prefix="/api/v1")
        client = TestClient(app)
        try:
            buffer = BytesIO()
            Image.new("RGB", (24, 24), "white").save(buffer, format="PNG")
            response = client.post(
                "/api/v1/generate/",
                files={"file": ("sample.png", buffer.getvalue(), "image/png")},
                data={
                    "platform": "Instagram", "language": "English", "style": "Creative",
                    "template": "instagram_creative",
                },
            )
            self.assertEqual(response.status_code, 200, response.text)
            listing = self.client.get("/api/v1/history/").json()
            self.assertEqual(listing["total"], 1)
            self.assertEqual(listing["records"][0]["visual_template"], "instagram_creative")

            omitted_template = client.post(
                "/api/v1/generate/",
                files={"file": ("sample.png", buffer.getvalue(), "image/png")},
                data={"platform": "Instagram", "language": "English", "style": "Creative"},
            )
            self.assertEqual(omitted_template.status_code, 200, omitted_template.text)
            listing = self.client.get("/api/v1/history/").json()
            self.assertEqual(listing["total"], 2)
            self.assertIsNone(listing["records"][0]["visual_template"])

            app.state.groq_service = FailingGroq()
            failed = client.post(
                "/api/v1/generate/",
                files={"file": ("sample.png", buffer.getvalue(), "image/png")},
                data={"platform": "Instagram", "language": "English", "style": "Creative"},
            )
            self.assertEqual(failed.status_code, 503)
            self.assertEqual(self.client.get("/api/v1/history/").json()["total"], 2)
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
