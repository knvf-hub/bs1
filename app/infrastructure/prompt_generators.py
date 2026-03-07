from __future__ import annotations

import json
from typing import Protocol

from app.domain.product_prompts import (
    ExtractedProduct,
    ProductAnalysis,
    PromptVariant,
)


class ProductPromptGenerator(Protocol):
    def generate(
        self,
        *,
        product: ExtractedProduct,
        target_platform: str,
        target_audiences: list[str],
        style_hint: str | None,
        prompt_count: int,
        auto_detect_audience: bool,
        auto_detect_style: bool,
        language: str,
    ) -> tuple[ProductAnalysis, list[PromptVariant]]:
        ...


class HeuristicPromptGenerator:
    DEFAULT_AUDIENCES = [
        "วัยทำงาน",
        "นักศึกษา",
        "สายแต่งห้อง",
        "สายมินิมอล",
    ]

    DEFAULT_STYLES = [
        "premium lifestyle",
        "minimal clean",
        "cozy home",
        "ugc creator style",
        "studio product ad",
    ]

    ANGLES = [
        "hero product shot",
        "lifestyle usage scene",
        "desk setup angle",
        "cozy home corner",
        "close-up detail shot",
        "ugc creator framing",
        "premium studio ad",
    ]

    def generate(
        self,
        *,
        product: ExtractedProduct,
        target_platform: str,
        target_audiences: list[str],
        style_hint: str | None,
        prompt_count: int,
        auto_detect_audience: bool,
        auto_detect_style: bool,
        language: str,
    ) -> tuple[ProductAnalysis, list[PromptVariant]]:
        title_lower = product.title.lower()

        detected_audiences = list(target_audiences)
        if auto_detect_audience or not detected_audiences:
            for keyword, audience in [
                ("โต๊ะ", "วัยทำงาน"),
                ("desk", "วัยทำงาน"),
                ("นักเรียน", "นักศึกษา"),
                ("student", "นักศึกษา"),
                ("ห้อง", "สายแต่งห้อง"),
                ("lamp", "สายแต่งห้อง"),
                ("minimal", "สายมินิมอล"),
            ]:
                if keyword in title_lower and audience not in detected_audiences:
                    detected_audiences.append(audience)

        if not detected_audiences:
            detected_audiences = self.DEFAULT_AUDIENCES[:3]

        detected_styles = []
        if style_hint:
            detected_styles.append(style_hint)

        if auto_detect_style or not detected_styles:
            if any(k in title_lower for k in ["แก้ว", "tumbler", "cup", "mug"]):
                detected_styles.extend(["premium lifestyle", "minimal clean", "ugc creator style"])
            elif any(k in title_lower for k in ["lamp", "โคม", "ไฟ", "light"]):
                detected_styles.extend(["cozy home", "minimal clean", "premium lifestyle"])
            else:
                detected_styles.extend(self.DEFAULT_STYLES[:3])

        # de-dup
        detected_styles = list(dict.fromkeys(detected_styles))

        analysis = ProductAnalysis(
            suggested_audiences=detected_audiences[:4],
            suggested_styles=detected_styles[:5],
            platform_strategy=self._platform_strategy(target_platform, language),
        )

        prompts: list[PromptVariant] = []
        for i in range(prompt_count):
            audience = detected_audiences[i % len(detected_audiences)]
            style = detected_styles[i % len(detected_styles)]
            angle = self.ANGLES[i % len(self.ANGLES)]

            prompts.append(
                PromptVariant(
                    index=i + 1,
                    title=self._build_title(i, language),
                    audience=audience,
                    style=style,
                    angle=angle,
                    prompt=self._build_prompt(
                        product_title=product.title,
                        audience=audience,
                        style=style,
                        angle=angle,
                        target_platform=target_platform,
                        language=language,
                    ),
                    negative_prompt=(
                        "blurry, low quality, extra objects, duplicate product, cropped product, "
                        "distorted shape, broken hands, extra fingers, watermark, text overlay, logo clutter"
                    ),
                )
            )

        return analysis, prompts

    def _platform_strategy(self, platform: str, language: str) -> str:
        if language == "th":
            if platform == "tiktok":
                return "ภาพควร hook เร็ว สินค้าเด่น องค์ประกอบชัด ใช้ scene ที่ดูใช้งานได้จริงและเหมาะกับ short-form content"
            return "ภาพควรชัด สื่อจุดเด่นสินค้าได้เร็ว และใช้ composition ที่พร้อมต่อยอดเป็นคอนเทนต์ขาย"
        return "Use strong product focus, fast visual hook, and ad-ready composition optimized for short-form content."

    def _build_title(self, idx: int, language: str) -> str:
        titles_th = [
            "ภาพสินค้าเด่นแบบโปร",
            "ภาพใช้งานจริงสไตล์ไลฟ์สไตล์",
            "ภาพมุมโต๊ะทำงาน",
            "ภาพโฮมมี่อบอุ่น",
            "ภาพโคลสอัปเน้นดีเทล",
            "ภาพครีเอเตอร์รีวิว",
            "ภาพโฆษณาสตูดิโอ",
        ]
        titles_en = [
            "Hero Product Shot",
            "Lifestyle Usage Scene",
            "Desk Setup Angle",
            "Cozy Home Scene",
            "Close-up Detail Shot",
            "UGC Creator Style",
            "Premium Studio Ad",
        ]
        arr = titles_th if language == "th" else titles_en
        return arr[idx % len(arr)]

    def _build_prompt(
        self,
        *,
        product_title: str,
        audience: str,
        style: str,
        angle: str,
        target_platform: str,
        language: str,
    ) -> str:
        if language == "th":
            return (
                f"สร้างภาพสินค้า '{product_title}' สำหรับกลุ่มเป้าหมาย {audience}, "
                f"โทนภาพ {style}, มุมภาพแบบ {angle}, "
                f"เน้นให้สินค้าเป็นจุดเด่นหลัก ภาพสวยแบบโฆษณา องค์ประกอบสะอาด ดูน่าเชื่อถือ "
                f"เหมาะสำหรับคอนเทนต์ {target_platform}, แสงสวย, รายละเอียดคมชัด, realistic, premium commercial photography"
            )

        return (
            f"Create an ad-ready image for the product '{product_title}' aimed at {audience}. "
            f"Style: {style}. Camera/composition: {angle}. "
            f"Make the product the clear hero subject, with clean composition, strong commercial appeal, "
            f"realistic lighting, sharp details, premium product advertising photography for {target_platform}."
        )


class OpenAIProductPromptGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def generate(
        self,
        *,
        product: ExtractedProduct,
        target_platform: str,
        target_audiences: list[str],
        style_hint: str | None,
        prompt_count: int,
        auto_detect_audience: bool,
        auto_detect_style: bool,
        language: str,
    ) -> tuple[ProductAnalysis, list[PromptVariant]]:
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key)

        schema = {
            "name": "product_prompt_pack",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "analysis": {
                        "type": "object",
                        "properties": {
                            "suggested_audiences": {"type": "array", "items": {"type": "string"}},
                            "suggested_styles": {"type": "array", "items": {"type": "string"}},
                            "platform_strategy": {"type": "string"},
                        },
                        "required": ["suggested_audiences", "suggested_styles", "platform_strategy"],
                        "additionalProperties": False,
                    },
                    "prompts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "index": {"type": "integer"},
                                "title": {"type": "string"},
                                "audience": {"type": "string"},
                                "style": {"type": "string"},
                                "angle": {"type": "string"},
                                "prompt": {"type": "string"},
                                "negative_prompt": {"type": "string"},
                            },
                            "required": [
                                "index",
                                "title",
                                "audience",
                                "style",
                                "angle",
                                "prompt",
                                "negative_prompt",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["analysis", "prompts"],
                "additionalProperties": False,
            },
        }

        user_input = {
            "product": product.model_dump(mode="json"),
            "target_platform": target_platform,
            "target_audiences": target_audiences,
            "style_hint": style_hint,
            "prompt_count": prompt_count,
            "auto_detect_audience": auto_detect_audience,
            "auto_detect_style": auto_detect_style,
            "language": language,
        }

        completion = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert product-ad prompt strategist. "
                        "Generate 5-7 high-quality, non-duplicate image prompts for product marketing. "
                        "Each prompt must differ in at least two dimensions among audience, scene, angle, lighting, mood, or composition. "
                        "Output valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(user_input, ensure_ascii=False),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": schema,
            },
            temperature=0.8,
        )

        raw = completion.choices[0].message.content
        if not raw:
            raise ValueError("OpenAI returned empty content")

        payload = json.loads(raw)

        analysis = ProductAnalysis.model_validate(payload["analysis"])
        prompts = [PromptVariant.model_validate(x) for x in payload["prompts"]]
        return analysis, prompts