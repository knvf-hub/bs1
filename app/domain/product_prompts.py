from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

SupportedPlatform = Literal["tiktok", "shopee", "facebook", "instagram"]
SupportedLanguage = Literal["th", "en"]


class GenerateProductPromptsRequest(BaseModel):
    product_url: HttpUrl
    target_platform: SupportedPlatform = "tiktok"
    target_audiences: list[str] = Field(default_factory=list)
    style_hint: str | None = None
    prompt_count: int = Field(default=5, ge=1, le=10)
    auto_detect_audience: bool = True
    auto_detect_style: bool = True
    language: SupportedLanguage = "th"


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
    image_asset_id: str | None = None
    image_asset_path: str | None = None


class ProductAnalysis(BaseModel):
    suggested_audiences: list[str] = Field(default_factory=list)
    suggested_styles: list[str] = Field(default_factory=list)
    platform_strategy: str


class GenerateProductPromptsResponse(BaseModel):
    product: ExtractedProduct
    analysis: ProductAnalysis
    prompts: list[PromptVariant]


class BatchGenerateProductPromptsItem(BaseModel):
    no: str | None = None
    name: str | None = None
    link: HttpUrl
    target: SupportedPlatform = "shopee"
    language: SupportedLanguage = "th"
    model: str | None = None


class BatchGenerateProductPromptsResult(BaseModel):
    no: str | None = None
    input_name: str | None = None
    target: SupportedPlatform
    language: SupportedLanguage
    selected_model: str | None = None
    product: ExtractedProduct
    analysis: ProductAnalysis
    prompts: list[PromptVariant]


class BatchGenerateProductPromptsResponse(BaseModel):
    total: int
    results: list[BatchGenerateProductPromptsResult]