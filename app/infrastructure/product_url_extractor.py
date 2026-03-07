from __future__ import annotations

import re
from urllib.parse import urlparse, unquote

from app.domain.product_prompts import ExtractedProduct
import logging

logger = logging.getLogger(__name__)

def _clean_title_from_slug(slug: str) -> str:
    text = slug.replace("-", " ").replace("_", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text or "สินค้าไม่มีชื่อ"


class ProductUrlExtractor:
    def extract(self, product_url: str) -> ExtractedProduct:
        logger.debug("Extracting product from URL: %s", product_url)
        parsed = urlparse(product_url)
        host = parsed.netloc.lower()
        path = unquote(parsed.path.strip("/"))
        logger.debug("Parsed URL: host=%s path=%s", parsed.netloc, parsed.path)

        if "shopee" in host:
            logger.debug("Detected Shopee URL")
            return self._extract_shopee(product_url, host, path)

        # fallback generic
        slug = path.split("/")[-1] if path else "product"
        title = _clean_title_from_slug(slug)
        logger.info("Extracted product title=%s from url=%s", title, product_url)

        return ExtractedProduct(
            source_url=product_url,
            source=host or "unknown",
            title=title,
            summary=None,
            image_urls=[],
            raw={"path": path},
        )

    def _extract_shopee(self, product_url: str, host: str, path: str) -> ExtractedProduct:
        # ตัวอย่าง path: some-product-name-i.12345.67890
        slug = path.split("/")[-1] if path else ""
        slug = re.sub(r"-i\.\d+\.\d+$", "", slug)
        title = _clean_title_from_slug(slug)

        return ExtractedProduct(
            source_url=product_url,
            source="shopee",
            title=title,
            summary=f"สินค้าจาก Shopee: {title}",
            image_urls=[],
            raw={"host": host, "path": path},
        )