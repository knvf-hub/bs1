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
        logger.debug("OpenAI generator is enabled with model=%s", settings.openai_prompt_model)
        return OpenAIProductPromptGenerator(
            api_key=settings.openai_api_key,
            model=settings.openai_prompt_model,
        )

    logger.debug("OpenAI generator is disabled, no API key configured")
    return None


def _build_heuristic_generator() -> HeuristicPromptGenerator:
    logger.debug("Using heuristic prompt generator")
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
    logger.info(
        "Start prompt generation: title=%s target=%s language=%s prompt_count=%s",
        product.title,
        target_platform,
        language,
        prompt_count,
    )

    openai_generator = _build_openai_generator()

    if openai_generator is not None:
        try:
            logger.debug(
                "Trying OpenAI generator: title=%s model=%s",
                product.title,
                settings.openai_prompt_model,
            )
            result = openai_generator.generate(
                product=product,
                target_platform=target_platform,
                target_audiences=target_audiences,
                style_hint=style_hint,
                prompt_count=prompt_count,
                auto_detect_audience=auto_detect_audience,
                auto_detect_style=auto_detect_style,
                language=language,
            )
            logger.info("OpenAI prompt generation succeeded: title=%s", product.title)
            return result
        except Exception as e:
            logger.warning(
                "OpenAI generator failed for title=%s, fallback to heuristic generator: %s",
                product.title,
                str(e),
            )

    heuristic_generator = _build_heuristic_generator()
    result = heuristic_generator.generate(
        product=product,
        target_platform=target_platform,
        target_audiences=target_audiences,
        style_hint=style_hint,
        prompt_count=prompt_count,
        auto_detect_audience=auto_detect_audience,
        auto_detect_style=auto_detect_style,
        language=language,
    )
    logger.info("Heuristic prompt generation succeeded: title=%s", product.title)
    return result


def _override_product_name(
    extracted: ExtractedProduct,
    name: str | None,
) -> ExtractedProduct:
    cleaned_name = (name or "").strip()
    if not cleaned_name:
        logger.debug(
            "No input name override, using extracted title=%s",
            extracted.title,
        )
        return extracted

    logger.info(
        "Override extracted product title: old=%s new=%s",
        extracted.title,
        cleaned_name,
    )
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

    logger.debug(
        "Attach image assets to prompts: prompt_count=%s preferred_model=%s",
        len(prompts),
        preferred_model,
    )

    for prompt in prompts:
        asset = choose_image_asset(
            style=prompt.style,
            audience=prompt.audience,
            angle=prompt.angle,
            preferred_model=preferred_model,
        )

        logger.debug(
            "Image asset selected for prompt index=%s title=%s style=%s audience=%s angle=%s asset=%s",
            prompt.index,
            prompt.title,
            prompt.style,
            prompt.audience,
            prompt.angle,
            asset.id if asset else None,
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

    logger.info(
        "Finished attaching image assets: selected_model=%s prompt_count=%s",
        selected_model,
        len(enriched),
    )
    return enriched, selected_model


def generate_product_prompts(
    req: GenerateProductPromptsRequest,
) -> GenerateProductPromptsResponse:
    logger.info(
        "Generate single product prompts: url=%s target=%s language=%s",
        req.product_url,
        req.target_platform,
        req.language,
    )

    extractor = ProductUrlExtractor()
    product = extractor.extract(str(req.product_url))

    logger.info(
        "Product extracted from single request: source=%s title=%s url=%s",
        product.source,
        product.title,
        product.source_url,
    )
    logger.debug("Extracted product raw data: %s", product.raw)

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

    prompts, selected_model = _attach_image_assets_to_prompts(prompts)

    logger.info(
        "Single product prompt generation completed: title=%s prompts=%s selected_model=%s",
        product.title,
        len(prompts),
        selected_model,
    )

    return GenerateProductPromptsResponse(
        product=product,
        analysis=analysis,
        prompts=prompts,
    )


def generate_product_prompts_from_row(
    item: BatchGenerateProductPromptsItem,
) -> BatchGenerateProductPromptsResult:
    logger.info(
        "Generate prompts from row: no=%s link=%s target=%s language=%s preferred_model=%s",
        item.no,
        item.link,
        item.target,
        item.language,
        item.model,
    )

    extractor = ProductUrlExtractor()
    extracted = extractor.extract(str(item.link))

    logger.info(
        "Row product extracted: no=%s source=%s title=%s",
        item.no,
        extracted.source,
        extracted.title,
    )
    logger.debug("Row extracted raw data: no=%s raw=%s", item.no, extracted.raw)

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

    logger.info(
        "Row prompt generation completed: no=%s title=%s prompts=%s selected_model=%s",
        item.no,
        product.title,
        len(prompts),
        selected_model,
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
    logger.info("Start batch product prompt generation: total_rows=%s", len(items))

    results: list[BatchGenerateProductPromptsResult] = []

    for item in items:
        try:
            result = generate_product_prompts_from_row(item)
            results.append(result)
        except Exception as e:
            logger.exception(
                "Failed to generate prompts for row no=%s link=%s: %s",
                item.no,
                item.link,
                str(e),
            )
            raise

    logger.info("Batch product prompt generation completed: total_results=%s", len(results))

    return BatchGenerateProductPromptsResponse(
        total=len(results),
        results=results,
    )