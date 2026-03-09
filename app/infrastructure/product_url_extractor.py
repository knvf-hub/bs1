from __future__ import annotations

import logging
import re
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup

from app.domain.product_prompts import ExtractedProduct

logger = logging.getLogger(__name__)


def _clean_title_from_slug(slug: str) -> str:
    text = slug.replace("-", " ").replace("_", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text or "สินค้าไม่มีชื่อ"


class ProductUrlExtractor:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
        }

    def extract(self, product_url: str) -> ExtractedProduct:
        logger.info("Extracting product from URL: %s", product_url)

        parsed = urlparse(product_url)
        host = parsed.netloc.lower()

        if "shopee" in host:
            return self._extract_shopee(product_url)

        return self._extract_generic(product_url)

    def _extract_generic(self, product_url: str) -> ExtractedProduct:
        parsed = urlparse(product_url)
        path = unquote(parsed.path.strip("/"))
        slug = path.split("/")[-1] if path else "product"
        title = _clean_title_from_slug(slug)

        logger.info("Generic extraction done: title=%s url=%s", title, product_url)

        return ExtractedProduct(
            source_url=product_url,
            source=parsed.netloc.lower() or "unknown",
            title=title,
            summary=None,
            final_url=product_url,
            title_slug=title,
            shop_id=None,
            item_id=None,
            image_url=None,
            image_urls=[],
            extraction_method="generic_slug",
            raw={
                "host": parsed.netloc.lower(),
                "path": parsed.path,
                "query": parsed.query,
            },
        )

    def _extract_shopee(self, product_url: str) -> ExtractedProduct:
        final_url = product_url
        html = None
        status_code = None

        try:
            response = self._session.get(
                product_url,
                headers=self._headers,
                timeout=15,
                allow_redirects=True,
            )
            response.raise_for_status()

            final_url = response.url
            html = response.text
            status_code = response.status_code

            logger.info(
                "Shopee URL resolved: original=%s final=%s status=%s",
                product_url,
                final_url,
                status_code,
            )
        except Exception as e:
            logger.warning(
                "Shopee fetch failed, fallback to URL parsing only. url=%s error=%s",
                product_url,
                str(e),
            )

        parsed = urlparse(final_url)
        path = unquote(parsed.path.strip("/"))

        title_slug, shop_id, item_id = self._parse_shopee_identity(path)

        meta_title = None
        meta_image = None
        image_urls: list[str] = []

        if html:
            meta_title, meta_image, image_urls = self._extract_meta_from_html(html)

        title = meta_title or title_slug or "สินค้าไม่มีชื่อ"
        image_url = meta_image or (image_urls[0] if image_urls else None)

        extraction_method = "shopee_meta" if (meta_title or meta_image) else "shopee_redirect_slug"

        logger.info(
            "Shopee extraction done: title=%s shop_id=%s item_id=%s image_url=%s method=%s",
            title,
            shop_id,
            item_id,
            image_url,
            extraction_method,
        )

        return ExtractedProduct(
            source_url=product_url,
            source="shopee",
            title=title,
            summary=f"สินค้าจาก Shopee: {title}",
            final_url=final_url,
            title_slug=title_slug,
            shop_id=shop_id,
            item_id=item_id,
            image_url=image_url,
            image_urls=image_urls,
            extraction_method=extraction_method,
            raw={
                "host": parsed.netloc.lower(),
                "path": parsed.path,
                "query": parsed.query,
                "status_code": status_code,
            },
        )

    def _parse_shopee_identity(self, path: str) -> tuple[str | None, str | None, str | None]:
        if not path:
            return None, None, None

        match = re.match(r"(?P<slug>.+)-i\.(?P<shop_id>\d+)\.(?P<item_id>\d+)$", path)

        if not match:
            slug = path.split("/")[-1] if path else ""
            title_slug = _clean_title_from_slug(slug) if slug else None
            return title_slug, None, None

        slug = match.group("slug")
        title_slug = _clean_title_from_slug(slug)
        shop_id = match.group("shop_id")
        item_id = match.group("item_id")

        return title_slug, shop_id, item_id

    def _extract_meta_from_html(self, html: str) -> tuple[str | None, str | None, list[str]]:
        soup = BeautifulSoup(html, "html.parser")

        title = (
            self._get_meta_content(soup, "property", "og:title")
            or self._get_meta_content(soup, "name", "twitter:title")
            or self._get_title_tag(soup)
        )

        image_candidates: list[str] = []

        for attr_name, attr_value in [
            ("property", "og:image"),
            ("name", "twitter:image"),
        ]:
            value = self._get_meta_content(soup, attr_name, attr_value)
            if value:
                image_candidates.append(value)

        image_candidates = list(dict.fromkeys(image_candidates))
        primary_image = image_candidates[0] if image_candidates else None

        return title, primary_image, image_candidates

    def _get_meta_content(
        self,
        soup: BeautifulSoup,
        attr_name: str,
        attr_value: str,
    ) -> str | None:
        tag = soup.find("meta", attrs={attr_name: attr_value})
        if not tag:
            return None

        content = tag.get("content")
        if not content:
            return None

        content = str(content).strip()
        return content or None

    def _get_title_tag(self, soup: BeautifulSoup) -> str | None:
        if not soup.title or not soup.title.string:
            return None

        title = soup.title.string.strip()
        return title or None