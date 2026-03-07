from __future__ import annotations

from app.core.config import settings
from app.domain.product_prompts import (
    GenerateProductPromptsRequest,
    GenerateProductPromptsResponse,
)
from app.infrastructure.product_url_extractor import ProductUrlExtractor
from app.infrastructure.prompt_generators import (
    HeuristicPromptGenerator,
    OpenAIProductPromptGenerator,
)


def _build_generator():
    if settings.openai_api_key:
        return OpenAIProductPromptGenerator(
            api_key=settings.openai_api_key,
            model=settings.openai_prompt_model,
        )
    return HeuristicPromptGenerator()


def generate_product_prompts(
    req: GenerateProductPromptsRequest,
) -> GenerateProductPromptsResponse:
    extractor = ProductUrlExtractor()
    product = extractor.extract(str(req.product_url))

    generator = _build_generator()
    analysis, prompts = generator.generate(
        product=product,
        target_platform=req.target_platform,
        target_audiences=req.target_audiences,
        style_hint=req.style_hint,
        prompt_count=req.prompt_count,
        auto_detect_audience=req.auto_detect_audience,
        auto_detect_style=req.auto_detect_style,
        language=req.language,
    )

    return GenerateProductPromptsResponse(
        product=product,
        analysis=analysis,
        prompts=prompts,
    )