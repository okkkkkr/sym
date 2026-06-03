from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "home_layout" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "page_code" VARCHAR(50) NOT NULL DEFAULT 'home',
    "status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "version" INT NOT NULL DEFAULT 0,
    "is_current" INT NOT NULL DEFAULT 0,
    "published_at" TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_home_layout_created_at" ON "home_layout" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_updated_at" ON "home_layout" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_page_code" ON "home_layout" ("page_code");
CREATE INDEX IF NOT EXISTS "idx_home_layout_status" ON "home_layout" ("status");
CREATE INDEX IF NOT EXISTS "idx_home_layout_version" ON "home_layout" ("version");
CREATE INDEX IF NOT EXISTS "idx_home_layout_is_current" ON "home_layout" ("is_current");
CREATE INDEX IF NOT EXISTS "idx_home_layout_published_at" ON "home_layout" ("published_at");
CREATE TABLE IF NOT EXISTS "home_layout_module" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "type" VARCHAR(50) NOT NULL,
    "sort" INT NOT NULL DEFAULT 0,
    "is_enabled" INT NOT NULL DEFAULT 1,
    "title" VARCHAR(255) NOT NULL DEFAULT '',
    "action" JSON NOT NULL,
    "config" JSON NOT NULL,
    "layout_id" BIGINT NOT NULL REFERENCES "home_layout" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_home_layout_module_created_at" ON "home_layout_module" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_module_updated_at" ON "home_layout_module" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_module_type" ON "home_layout_module" ("type");
CREATE INDEX IF NOT EXISTS "idx_home_layout_module_sort" ON "home_layout_module" ("sort");
CREATE INDEX IF NOT EXISTS "idx_home_layout_module_is_enabled" ON "home_layout_module" ("is_enabled");
CREATE INDEX IF NOT EXISTS "idx_home_layout_module_layout_id" ON "home_layout_module" ("layout_id");
CREATE TABLE IF NOT EXISTS "home_layout_item" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "sort" INT NOT NULL DEFAULT 0,
    "image" VARCHAR(500) NOT NULL DEFAULT '',
    "title" VARCHAR(255) NOT NULL DEFAULT '',
    "description" VARCHAR(500) NOT NULL DEFAULT '',
    "badge" VARCHAR(100) NOT NULL DEFAULT '',
    "action" JSON NOT NULL,
    "module_id" BIGINT NOT NULL REFERENCES "home_layout_module" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_home_layout_item_created_at" ON "home_layout_item" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_item_updated_at" ON "home_layout_item" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_item_sort" ON "home_layout_item" ("sort");
CREATE INDEX IF NOT EXISTS "idx_home_layout_item_module_id" ON "home_layout_item" ("module_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "home_layout_item";
        DROP TABLE IF EXISTS "home_layout_module";
        DROP TABLE IF EXISTS "home_layout";
    """
