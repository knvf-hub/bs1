from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_product_prompts():
    payload = {
        "product_url": "https://shopee.co.th/แก้วน้ำเก็บอุณหภูมิสีครีม-i.12345.67890",
        "target_platform": "tiktok",
        "target_audiences": ["วัยทำงาน", "นักศึกษา"],
        "style_hint": None,
        "prompt_count": 5,
        "auto_detect_audience": True,
        "auto_detect_style": True,
        "language": "th",
    }

    res = client.post("/api/v1/product-prompts/generate", json=payload)
    assert res.status_code == 200

    body = res.json()
    assert body["product"]["source"] == "shopee"
    assert body["product"]["title"] != ""
    assert len(body["prompts"]) == 5

    first = body["prompts"][0]
    assert "prompt" in first
    assert "negative_prompt" in first
    assert first["prompt"] != ""