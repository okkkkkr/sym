from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "contact" ADD "is_deleted" INT NOT NULL DEFAULT 0;
        ALTER TABLE "contact" ADD "deleted_at" TIMESTAMP;
CREATE INDEX IF NOT EXISTS "idx_contact_is_deleted" ON "contact" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_contact_deleted_at" ON "contact" ("deleted_at");
CREATE TABLE IF NOT EXISTS "contact_click" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "visitor_id" VARCHAR(64) NOT NULL,
    "contact_id" BIGINT NOT NULL,
    "platform_snapshot" VARCHAR(50) NOT NULL,
    "display_name_snapshot" VARCHAR(100) NOT NULL,
    "contact_type_snapshot" VARCHAR(30),
    "contact_value_snapshot" VARCHAR(255),
    "link_url_snapshot" VARCHAR(500),
    "clicked_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_contact_click_visitor_id" ON "contact_click" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_contact_click_contact_id" ON "contact_click" ("contact_id");
CREATE INDEX IF NOT EXISTS "idx_contact_click_contact_type_snapshot" ON "contact_click" ("contact_type_snapshot");
CREATE INDEX IF NOT EXISTS "idx_contact_click_clicked_at" ON "contact_click" ("clicked_at");
CREATE TABLE IF NOT EXISTS "contact_click_dedup" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "visitor_id" VARCHAR(64) NOT NULL,
    "contact_id" BIGINT NOT NULL,
    "last_counted_at" TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_contact_click_dedup_visitor_id" ON "contact_click_dedup" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_contact_click_dedup_contact_id" ON "contact_click_dedup" ("contact_id");
CREATE INDEX IF NOT EXISTS "idx_contact_click_dedup_last_counted_at" ON "contact_click_dedup" ("last_counted_at");
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_contact_click_dedup_visitor_contact" ON "contact_click_dedup" ("visitor_id", "contact_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "contact_click_dedup";
        DROP TABLE IF EXISTS "contact_click";
        DROP INDEX IF EXISTS "idx_contact_is_deleted";
        DROP INDEX IF EXISTS "idx_contact_deleted_at";
    """
