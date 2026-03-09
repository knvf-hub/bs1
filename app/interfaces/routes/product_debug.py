from fastapi import APIRouter, Query

from app.infrastructure.product_fetchers.shopee_fetcher import ShopeeProductFetcher

router = APIRouter()


@router.get("/debug/fetch-product")
def fetch_product(
    url: str | None = Query(default=None),
    path: str | None = Query(default=None),
):
    fetcher = ShopeeProductFetcher()

    if url:
        product = fetcher.fetch(url)
        return {"product": product}

    if path:
        product = fetcher.fetch_from_path(path)
        return {"product": product}

    return {
        "product": None,
        "error": "please provide either 'url' or 'path'",
    }