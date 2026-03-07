from fastapi import APIRouter

from app.application.product_prompts import generate_product_prompts
from app.domain.product_prompts import (
    GenerateProductPromptsRequest,
    GenerateProductPromptsResponse,
)

router = APIRouter(prefix="/product-prompts", tags=["product-prompts"])


@router.post("/generate", response_model=GenerateProductPromptsResponse)
def post_generate_product_prompts(
    req: GenerateProductPromptsRequest,
) -> GenerateProductPromptsResponse:
    return generate_product_prompts(req)