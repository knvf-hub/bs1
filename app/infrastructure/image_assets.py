from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImageAsset:
    id: str
    file_name: str
    file_path: str
    asset_type: str
    tags: list[str]


def load_image_assets() -> list[ImageAsset]:
    base = Path("assets/models")
    assets: list[ImageAsset] = []

    if not base.exists():
        return assets

    for path in sorted(base.glob("*")):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue

        stem = path.stem.lower()
        tags = stem.split("_")

        asset_type = "unknown"
        if "man" in tags:
            asset_type = "man"
        elif "woman" in tags or "women" in tags:
            asset_type = "woman"
        elif "couple" in tags:
            asset_type = "couple"
        elif "dog" in tags or "shiba" in tags:
            asset_type = "dog"

        assets.append(
            ImageAsset(
                id=path.stem,
                file_name=path.name,
                file_path=str(path),
                asset_type=asset_type,
                tags=tags,
            )
        )

    return assets


def get_image_asset_by_id(asset_id: str) -> ImageAsset | None:
    target = asset_id.strip().lower()
    for asset in load_image_assets():
        if asset.id.lower() == target:
            return asset
    return None


def choose_image_asset(
    *,
    style: str,
    audience: str,
    angle: str,
    preferred_model: str | None = None,
) -> ImageAsset | None:
    assets = load_image_assets()
    if not assets:
        return None

    if preferred_model:
        exact = get_image_asset_by_id(preferred_model)
        if exact is not None:
            return exact

    style_l = style.lower()
    audience_l = audience.lower()
    angle_l = angle.lower()

    def score(asset: ImageAsset) -> int:
        s = 0
        tags = set(asset.tags)

        if "review" in style_l or "review" in angle_l:
            if "review" in tags:
                s += 4

        if "city" in style_l or "office" in style_l or "desk" in angle_l:
            if "city" in tags or "office" in tags:
                s += 3

        if "cozy" in style_l or "home" in style_l or "life" in style_l:
            if "life" in tags or "local" in tags or "natural" in tags:
                s += 3

        if "premium" in style_l:
            if "city" in tags or "review" in tags:
                s += 2

        if "วัยทำงาน" in audience_l:
            if "office" in tags or "city" in tags:
                s += 2

        if "นักศึกษา" in audience_l:
            if "review" in tags or "local" in tags:
                s += 1

        if "man" in tags:
            s += 1

        return s

    ranked = sorted(assets, key=score, reverse=True)
    return ranked[0] if ranked else None