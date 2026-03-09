from fastapi import APIRouter
from app.infrastructure.product_fetchers.shopee_fetcher import ShopeeProductFetcher

router = APIRouter()

@router.get("/debug/fetch-product")
def fetch_product(url: str):
    fetcher = ShopeeProductFetcher()

    product = fetcher.fetch(url)

    return {
        "product": product
    }