from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


SupportedPlatform = Literal["tiktok", "shopee", "facebook", "instagram"]


class GenerateProductPromptsRequest(BaseModel):
    product_url: HttpUrl
    target_platform: SupportedPlatform = "tiktok"
    target_audiences: list[str] = Field(default_factory=list)
    style_hint: str | None = None
    prompt_count: int = Field(default=7, ge=1, le=7)
    auto_detect_audience: bool = True
    auto_detect_style: bool = True
    language: Literal["th", "en"] = "th"


class ExtractedProduct(BaseModel):
    source_url: HttpUrl
    source: str
    title: str
    summary: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict)


class PromptVariant(BaseModel):
    index: int
    title: str
    audience: str
    style: str
    angle: str
    prompt: str
    negative_prompt: str


class ProductAnalysis(BaseModel):
    suggested_audiences: list[str] = Field(default_factory=list)
    suggested_styles: list[str] = Field(default_factory=list)
    platform_strategy: str


class GenerateProductPromptsResponse(BaseModel):
    product: ExtractedProduct
    analysis: ProductAnalysis
    prompts: list[PromptVariant]