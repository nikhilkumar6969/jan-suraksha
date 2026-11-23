"""
PWA Readiness and Compliance Test Suite
Validates manifest.json, sw.js pre-cache assets, offline fallback, and security headers.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_manifest_json_structure():
    manifest_file = FRONTEND_DIR / "manifest.json"
    assert manifest_file.exists(), "manifest.json must exist in frontend/"
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("name") == "Jan Suraksha — Cyber Fraud & Scam Defense"
    assert data.get("short_name") == "Jan Suraksha"
    assert data.get("display") == "standalone"
    assert data.get("start_url") == "/"
    assert data.get("theme_color") == "#1e40af"
    assert data.get("background_color") == "#0f172a"
    assert "portrait-primary" in data.get("orientation", "")

    # Icons validation
    icons = data.get("icons", [])
    assert len(icons) >= 2, "Manifest must specify at least 192x192 and 512x512 icons"
    icon_sizes = [i.get("sizes") for i in icons]
    assert "192x192" in icon_sizes
    assert "512x512" in icon_sizes

    # Check maskable declaration
    has_maskable = any("maskable" in i.get("purpose", "") for i in icons)
    assert has_maskable, "Manifest must include maskable icon declaration"

    # Shortcuts validation
    shortcuts = data.get("shortcuts", [])
    assert len(shortcuts) >= 1, "Manifest should define app shortcuts"

def test_manifest_icons_exist_on_disk():
    manifest_file = FRONTEND_DIR / "manifest.json"
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for icon in data.get("icons", []):
        rel_path = icon["src"].lstrip("/")
        full_path = FRONTEND_DIR / rel_path
        assert full_path.exists(), f"Icon referenced in manifest does not exist: {icon['src']}"

def test_offline_fallback_html_exists():
    offline_file = FRONTEND_DIR / "offline.html"
    assert offline_file.exists(), "offline.html must exist in frontend/"
    with open(offline_file, "r", encoding="utf-8") as f:
        html = f.read()
    assert "Jan Suraksha" in html or "जन सुरक्षा" in html
    assert "ऑफ़लाइन" in html or "ऑफलाइन" in html or "Offline" in html

def test_service_worker_file_validity():
    sw_file = FRONTEND_DIR / "sw.js"
    assert sw_file.exists(), "sw.js must exist in frontend/"
    with open(sw_file, "r", encoding="utf-8") as f:
        sw_code = f.read()

    assert "CACHE_NAME" in sw_code
    assert "offline.html" in sw_code
    assert "index.html" in sw_code
    assert "skipWaiting" in sw_code
    assert "clients.claim" in sw_code

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "healthy"
    assert data.get("service") == "jan-suraksha"

def test_offline_page_endpoint(client):
    res = client.get("/offline.html")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")

def test_manifest_endpoint(client):
    res = client.get("/manifest.json")
    assert res.status_code == 200
    assert "json" in res.headers.get("content-type", "")
    data = res.json()
    assert data["short_name"] == "Jan Suraksha"

def test_security_headers_middleware(client):
    res = client.get("/health")
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "SAMEORIGIN"
    assert res.headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-origin" in res.headers.get("referrer-policy", "")
