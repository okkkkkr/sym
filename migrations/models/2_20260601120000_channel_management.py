from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "platform" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "platform_name" VARCHAR(100) NOT NULL,
    "custom_name" VARCHAR(50) NOT NULL UNIQUE,
    "click_count" INT NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS "idx_platform_created_at" ON "platform" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_platform_updated_at" ON "platform" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_platform_platform_name" ON "platform" ("platform_name");
CREATE INDEX IF NOT EXISTS "idx_platform_custom_name" ON "platform" ("custom_name");
CREATE INDEX IF NOT EXISTS "idx_platform_click_count" ON "platform" ("click_count");
CREATE TABLE IF NOT EXISTS "channel_visit" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "visitor_id" VARCHAR(64) NOT NULL,
    "platform_name_snapshot" VARCHAR(100) NOT NULL,
    "custom_name" VARCHAR(50) NOT NULL,
    "visited_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_channel_visit_visitor_id" ON "channel_visit" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_channel_visit_custom_name" ON "channel_visit" ("custom_name");
CREATE INDEX IF NOT EXISTS "idx_channel_visit_visited_at" ON "channel_visit" ("visited_at");
CREATE TABLE IF NOT EXISTS "channel_visit_dedup" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "visitor_id" VARCHAR(64) NOT NULL,
    "custom_name" VARCHAR(50) NOT NULL,
    "last_counted_at" TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_channel_visit_dedup_visitor_id" ON "channel_visit_dedup" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_channel_visit_dedup_custom_name" ON "channel_visit_dedup" ("custom_name");
CREATE INDEX IF NOT EXISTS "idx_channel_visit_dedup_last_counted_at" ON "channel_visit_dedup" ("last_counted_at");
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_channel_visit_dedup_visitor_custom" ON "channel_visit_dedup" ("visitor_id", "custom_name");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "channel_visit_dedup";
        DROP TABLE IF EXISTS "channel_visit";
        DROP TABLE IF EXISTS "platform";
    """
