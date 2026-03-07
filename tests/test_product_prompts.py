from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_product_prompts():
    payload = {
        "product_url": "https://s.shopee.co.th/1BHQ6Vr75e",
        "target_platform": "tiktok",
        "target_audiences": ["วัยทำงาน", "นักศึกษา"],
        "style_hint": None,
        "prompt_count": 5,
        "auto_detect_audience": True,
        "auto_detect_style": True,
        "language": "th",
    }

    response = client.post("/api/v1/product-prompts/generate", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert "product" in body
    assert "analysis" in body
    assert "prompts" in body

    product = body["product"]
    assert product["source"] == "shopee"
    assert isinstance(product["title"], str)
    assert product["title"].strip() != ""

    analysis = body["analysis"]
    assert "suggested_audiences" in analysis
    assert "suggested_styles" in analysis
    assert "platform_strategy" in analysis
    assert isinstance(analysis["platform_strategy"], str)
    assert analysis["platform_strategy"].strip() != ""

    prompts = body["prompts"]
    assert isinstance(prompts, list)
    assert len(prompts) == 5

    first = prompts[0]
    assert "index" in first
    assert "title" in first
    assert "audience" in first
    assert "style" in first
    assert "angle" in first
    assert "prompt" in first
    assert "negative_prompt" in first

    assert isinstance(first["index"], int)
    assert isinstance(first["title"], str)
    assert isinstance(first["audience"], str)
    assert isinstance(first["style"], str)
    assert isinstance(first["angle"], str)
    assert isinstance(first["prompt"], str)
    assert isinstance(first["negative_prompt"], str)

    assert first["prompt"].strip() != ""
    assert first["negative_prompt"].strip() != ""