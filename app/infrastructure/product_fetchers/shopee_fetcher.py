import logging
import re
from urllib.parse import unquote, urlparse

import requests

from app.domain.product_identity import ProductIdentity

logger = logging.getLogger(__name__)


class ShopeeProductFetcher:
    def resolve_url(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15,
            allow_redirects=True,
        )
        response.raise_for_status()
        return response.url

    def parse_product_identity(
        self,
        *,
        original_url: str,
        final_url: str,
    ) -> ProductIdentity:
        parsed = urlparse(final_url)
        decoded_path = unquote(parsed.path).strip("/")

        match = re.match(r"(?P<slug>.+)-i\.(?P<shop_id>\d+)\.(?P<item_id>\d+)$", decoded_path)

        title_slug = None
        shop_id = None
        item_id = None

        if match:
            title_slug = match.group("slug").replace("-", " ").strip()
            shop_id = match.group("shop_id")
            item_id = match.group("item_id")

        return ProductIdentity(
            original_url=original_url,
            final_url=final_url,
            path=parsed.path,
            query=parsed.query,
            source="shopee",
            method="redirect_resolve_plus_slug",
            title_slug=title_slug,
            shop_id=shop_id,
            item_id=item_id,
        )

    def fetch(self, url: str) -> dict | None:
        try:
            final_url = self.resolve_url(url)
            product = self.parse_product_identity(
                original_url=url,
                final_url=final_url,
            )

            logger.info("Fetched Shopee product row: %s", product)

            return {
                "original_url": product.original_url,
                "final_url": product.final_url,
                "path": product.path,
                "query": product.query,
                "source": product.source,
                "method": product.method,
                "title_slug": product.title_slug,
                "shop_id": product.shop_id,
                "item_id": product.item_id,
            }
        except Exception as e:
            logger.exception("Failed to fetch Shopee product. url=%s error=%s", url, e)
            return None