from urllib.parse import urlsplit

from tortoise import BaseDBAsyncClient


DEFAULT_CONTACT_QR_IMAGE_URL = "https://os.alipayobjects.com/rmsportal/QBnOOoLaAfKPirc.png"


def normalize_contact_qr_image_url(value: str | None) -> str:
    normalized = str(value or "").strip()
    if not normalized or normalized == DEFAULT_CONTACT_QR_IMAGE_URL:
        return ""
    if not normalized.startswith(("http://", "https://")):
        return normalized.lstrip("/")

    path = urlsplit(normalized).path.lstrip("/")
    if path.startswith("uploads/contacts/"):
        return path[len("uploads/") :]
    if path.startswith("contacts/"):
        return path
    return normalized


async def upgrade(db: BaseDBAsyncClient) -> str:
    for row in await db.execute_query_dict('SELECT "id", "qr_image_url" FROM "contact"'):
        await db.execute_query(
            'UPDATE "contact" SET "qr_image_url"=? WHERE "id"=?',
            [normalize_contact_qr_image_url(row.get("qr_image_url")), row["id"]],
        )

    return ""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return ""
