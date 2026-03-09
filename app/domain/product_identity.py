from dataclasses import dataclass


@dataclass
class ProductIdentity:
    original_url: str
    final_url: str
    path: str
    query: str
    source: str
    method: str
    title_slug: str | None
    shop_id: str | None
    item_id: str | None