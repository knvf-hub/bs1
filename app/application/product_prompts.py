from __future__ import annotations

import logging

from app.core.config import settings
from app.domain.product_prompts import (
    BatchGenerateProductPromptsItem,
    BatchGenerateProductPromptsResponse,
    BatchGenerateProductPromptsResult,
    ExtractedProduct,
    GenerateProductPromptsRequest,
    GenerateProductPromptsResponse,
    PromptVariant,
)
from app.infrastructure.image_assets import choose_image_asset
from app.infrastructure.product_url_extractor import ProductUrlExtractor
from app.infrastructure.prompt_generators import (
    HeuristicPromptGenerator,
    OpenAIProductPromptGenerator,
)

logger = logging.getLogger(__name__)

FIXED_STYLE_HINT: str | None = None
FIXED_PROMPT_COUNT = 5


def _build_openai_generator() -> OpenAIProductPromptGenerator | None:
    if settings.openai_api_key:
        return OpenAIProductPromptGenerator(
            api_key=settings.openai_api_key,
            model=settings.openai_prompt_model,
        )
    return None


def _build_heuristic_generator() -> HeuristicPromptGenerator:
    return HeuristicPromptGenerator()


def _generate_with_fallback(
    *,
    product: ExtractedProduct,
    target_platform: str,
    target_audiences: list[str],
    style_hint: str | None,
    prompt_count: int,
    auto_detect_audience: bool,
    auto_detect_style: bool,
    language: str,
):
    openai_generator = _build_openai_generator()

    if openai_generator is not None:
        try:
            return openai_generator.generate(
                product=product,
                target_platform=target_platform,
                target_audiences=target_audiences,
                style_hint=style_hint,
                prompt_count=prompt_count,
                auto_detect_audience=auto_detect_audience,
                auto_detect_style=auto_detect_style,
                language=language,
            )
        except Exception as e:
            logger.warning(
                "OpenAI generator failed, fallback to heuristic generator: %s",
                str(e),
            )

    heuristic_generator = _build_heuristic_generator()
    return heuristic_generator.generate(
        product=product,
        target_platform=target_platform,
        target_audiences=target_audiences,
        style_hint=style_hint,
        prompt_count=prompt_count,
        auto_detect_audience=auto_detect_audience,
        auto_detect_style=auto_detect_style,
        language=language,
    )


def _override_product_name(
    extracted: ExtractedProduct,
    name: str | None,
) -> ExtractedProduct:
    cleaned_name = (name or "").strip()
    if not cleaned_name:
        return extracted

    return ExtractedProduct(
        source_url=extracted.source_url,
        source=extracted.source,
        title=cleaned_name,
        summary=extracted.summary,
        image_urls=extracted.image_urls,
        raw=extracted.raw,
    )


def _attach_image_assets_to_prompts(
    prompts: list[PromptVariant],
    preferred_model: str | None = None,
) -> tuple[list[PromptVariant], str | None]:
    enriched: list[PromptVariant] = []
    selected_model: str | None = None

    for prompt in prompts:
        asset = choose_image_asset(
            style=prompt.style,
            audience=prompt.audience,
            angle=prompt.angle,
            preferred_model=preferred_model,
        )

        updated = prompt.model_copy(
            update={
                "image_asset_id": asset.id if asset else None,
                "image_asset_path": asset.file_path if asset else None,
            }
        )
        enriched.append(updated)

        if selected_model is None and asset is not None:
            selected_model = asset.id

    return enriched, selected_model


def generate_product_prompts(
    req: GenerateProductPromptsRequest,
) -> GenerateProductPromptsResponse:
    extractor = ProductUrlExtractor()
    product = extractor.extract(str(req.product_url))

    analysis, prompts = _generate_with_fallback(
        product=product,
        target_platform=req.target_platform,
        target_audiences=req.target_audiences,
        style_hint=req.style_hint,
        prompt_count=req.prompt_count,
        auto_detect_audience=req.auto_detect_audience,
        auto_detect_style=req.auto_detect_style,
        language=req.language,
    )

    prompts, _ = _attach_image_assets_to_prompts(prompts)

    return GenerateProductPromptsResponse(
        product=product,
        analysis=analysis,
        prompts=prompts,
    )


def generate_product_prompts_from_row(
    item: BatchGenerateProductPromptsItem,
) -> BatchGenerateProductPromptsResult:
    extractor = ProductUrlExtractor()
    extracted = extractor.extract(str(item.link))
    product = _override_product_name(extracted, item.name)

    analysis, prompts = _generate_with_fallback(
        product=product,
        target_platform=item.target,
        target_audiences=[],
        style_hint=FIXED_STYLE_HINT,
        prompt_count=FIXED_PROMPT_COUNT,
        auto_detect_audience=True,
        auto_detect_style=True,
        language=item.language,
    )

    prompts, selected_model = _attach_image_assets_to_prompts(
        prompts,
        preferred_model=item.model,
    )

    return BatchGenerateProductPromptsResult(
        no=item.no,
        input_name=item.name,
        target=item.target,
        language=item.language,
        selected_model=selected_model,
        product=product,
        analysis=analysis,
        prompts=prompts,
    )


def generate_product_prompts_from_rows(
    items: list[BatchGenerateProductPromptsItem],
) -> BatchGenerateProductPromptsResponse:
    results = [generate_product_prompts_from_row(item) for item in items]
    return BatchGenerateProductPromptsResponse(
        total=len(results),
        results=results,
    )