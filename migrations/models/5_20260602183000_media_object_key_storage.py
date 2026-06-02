import json
from urllib.parse import urlsplit

from tortoise import BaseDBAsyncClient


def normalize_object_key(value: str | None) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""

    if normalized.startswith(("http://", "https://")):
        path = urlsplit(normalized).path.lstrip("/")
    elif normalized.startswith("/uploads/"):
        path = normalized[len("/uploads/") :]
    else:
        path = normalized.lstrip("/")

    if path.startswith("uploads/"):
        return path[len("uploads/") :]
    return path


def normalize_object_key_list(value: str | None) -> str:
    if not value:
        return "[]"

    try:
        items = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid media key json: {value}") from exc

    if not isinstance(items, list):
        raise RuntimeError(f"Expected list json for media keys: {value}")

    return json.dumps([normalize_object_key(item) for item in items], ensure_ascii=False, separators=(",", ":"))


async def upgrade(db: BaseDBAsyncClient) -> str:
    await db.execute_script(
        """
        ALTER TABLE "site_config" RENAME COLUMN "logo_url" TO "logo_key";
        ALTER TABLE "product" RENAME COLUMN "cover_image_url" TO "cover_image_key";
        ALTER TABLE "product" RENAME COLUMN "image_urls" TO "image_keys";
        ALTER TABLE "product" RENAME COLUMN "video_urls" TO "video_keys";
        """
    )

    for row in await db.execute_query_dict('SELECT "id", "logo_key" FROM "site_config"'):
        await db.execute_query(
            'UPDATE "site_config" SET "logo_key"=? WHERE "id"=?',
            [normalize_object_key(row.get("logo_key")), row["id"]],
        )

    for row in await db.execute_query_dict(
        'SELECT "id", "cover_image_key", "image_keys", "video_keys" FROM "product"'
    ):
        await db.execute_query(
            'UPDATE "product" SET "cover_image_key"=?, "image_keys"=?, "video_keys"=? WHERE "id"=?',
            [
                normalize_object_key(row.get("cover_image_key")),
                normalize_object_key_list(row.get("image_keys")),
                normalize_object_key_list(row.get("video_keys")),
                row["id"],
            ],
        )

    return ""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "site_config" RENAME COLUMN "logo_key" TO "logo_url";
        ALTER TABLE "product" RENAME COLUMN "cover_image_key" TO "cover_image_url";
        ALTER TABLE "product" RENAME COLUMN "image_keys" TO "image_urls";
        ALTER TABLE "product" RENAME COLUMN "video_keys" TO "video_urls";
    """
