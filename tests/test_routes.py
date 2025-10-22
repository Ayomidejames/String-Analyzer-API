# tests/test_routes.py
import json
from app import create_app

app = create_app()
client = app.test_client()

def test_post_and_get_string():
    response = client.post(
        "/strings/",
        json={"value": "Level"},
        content_type="application/json"
    )
    assert response.status_code in (201, 409)

    # Try to retrieve the same string
    response = client.get("/strings/Level")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.get_json()
        assert "properties" in data
