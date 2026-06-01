from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "site_config" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "logo_url" VARCHAR(500) NOT NULL DEFAULT '',
    "about_title" VARCHAR(100) NOT NULL DEFAULT '',
    "about_lines" JSON NOT NULL,
    "footer_disclaimer" VARCHAR(500) NOT NULL DEFAULT '',
    "share_base_url" VARCHAR(500) NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS "idx_site_config_created_at" ON "site_config" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_site_config_updated_at" ON "site_config" ("updated_at");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "site_config";
    """
