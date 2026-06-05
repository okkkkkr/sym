from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        PRAGMA foreign_keys=OFF;

        ALTER TABLE "category" RENAME TO "category__old";
        CREATE TABLE "category" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "name" VARCHAR(50) NOT NULL UNIQUE,
            "desc" VARCHAR(255),
            "order" INT,
            "is_active" INT NOT NULL DEFAULT 1
        );
        INSERT INTO "category" ("id", "created_at", "updated_at", "name", "desc", "order", "is_active")
        SELECT "id", "created_at", "updated_at", "name", "desc", NULLIF("order", 0), "is_active"
        FROM "category__old";
        DROP TABLE "category__old";
        CREATE INDEX IF NOT EXISTS "idx_category_created_1d8a13" ON "category" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_category_updated_446ede" ON "category" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_category_name_8b0cb9" ON "category" ("name");
        CREATE INDEX IF NOT EXISTS "idx_category_order_ebae39" ON "category" ("order");
        CREATE INDEX IF NOT EXISTS "idx_category_is_acti_16ce8c" ON "category" ("is_active");

        ALTER TABLE "tag" RENAME TO "tag__old";
        CREATE TABLE "tag" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "name" VARCHAR(100) NOT NULL UNIQUE,
            "remark" VARCHAR(255),
            "search_count" INT NOT NULL DEFAULT 0,
            "sort" INT,
            "is_active" INT NOT NULL DEFAULT 1
        );
        INSERT INTO "tag" ("id", "created_at", "updated_at", "name", "remark", "search_count", "sort", "is_active")
        SELECT "id", "created_at", "updated_at", "name", "remark", "search_count", NULLIF("sort", 0), "is_active"
        FROM "tag__old";
        DROP TABLE "tag__old";
        CREATE INDEX IF NOT EXISTS "idx_tag_created_e4e466" ON "tag" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_tag_updated_fb661e" ON "tag" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_tag_name_a7b9a6" ON "tag" ("name");
        CREATE INDEX IF NOT EXISTS "idx_tag_search__566698" ON "tag" ("search_count");
        CREATE INDEX IF NOT EXISTS "idx_tag_sort_73ff0f" ON "tag" ("sort");
        CREATE INDEX IF NOT EXISTS "idx_tag_is_acti_50cf59" ON "tag" ("is_active");

        ALTER TABLE "brand" RENAME TO "brand__old";
        CREATE TABLE "brand" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "name" VARCHAR(100) NOT NULL,
            "desc" VARCHAR(255),
            "search_count" INT NOT NULL DEFAULT 0,
            "order" INT,
            "is_active" INT NOT NULL DEFAULT 1
        );
        INSERT INTO "brand" ("id", "created_at", "updated_at", "name", "desc", "search_count", "order", "is_active")
        SELECT "id", "created_at", "updated_at", "name", "desc", "search_count", NULLIF("order", 0), "is_active"
        FROM "brand__old";
        DROP TABLE "brand__old";
        CREATE INDEX IF NOT EXISTS "idx_brand_created_882788" ON "brand" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_brand_updated_959589" ON "brand" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_brand_name_c4e2df" ON "brand" ("name");
        CREATE INDEX IF NOT EXISTS "idx_brand_search__39fa28" ON "brand" ("search_count");
        CREATE INDEX IF NOT EXISTS "idx_brand_order_0a0d90" ON "brand" ("order");
        CREATE INDEX IF NOT EXISTS "idx_brand_is_acti_c5b780" ON "brand" ("is_active");

        ALTER TABLE "contact" RENAME TO "contact__old";
        CREATE TABLE "contact" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "platform" VARCHAR(50) NOT NULL,
            "display_name" VARCHAR(100) NOT NULL,
            "contact_type" VARCHAR(30),
            "contact_value" VARCHAR(255),
            "link_url" VARCHAR(500),
            "qr_image_url" VARCHAR(500),
            "order" INT,
            "is_active" INT NOT NULL DEFAULT 1,
            "is_deleted" INT NOT NULL DEFAULT 0,
            "deleted_at" TIMESTAMP
        );
        INSERT INTO "contact" (
            "id", "created_at", "updated_at", "platform", "display_name", "contact_type", "contact_value",
            "link_url", "qr_image_url", "order", "is_active", "is_deleted", "deleted_at"
        )
        SELECT
            "id", "created_at", "updated_at", "platform", "display_name", "contact_type", "contact_value",
            "link_url", "qr_image_url", NULLIF("order", 0), "is_active", "is_deleted", "deleted_at"
        FROM "contact__old";
        DROP TABLE "contact__old";
        CREATE INDEX IF NOT EXISTS "idx_contact_created_edee29" ON "contact" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_contact_updated_b40825" ON "contact" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_contact_platfor_0b6de8" ON "contact" ("platform");
        CREATE INDEX IF NOT EXISTS "idx_contact_display_f0b8bd" ON "contact" ("display_name");
        CREATE INDEX IF NOT EXISTS "idx_contact_contact_1715cc" ON "contact" ("contact_type");
        CREATE INDEX IF NOT EXISTS "idx_contact_order_ea68b2" ON "contact" ("order");
        CREATE INDEX IF NOT EXISTS "idx_contact_is_acti_87f467" ON "contact" ("is_active");
        CREATE INDEX IF NOT EXISTS "idx_contact_is_deleted" ON "contact" ("is_deleted");
        CREATE INDEX IF NOT EXISTS "idx_contact_deleted_at" ON "contact" ("deleted_at");
        CREATE INDEX IF NOT EXISTS "idx_contact_is_dele_808a7b" ON "contact" ("is_deleted");
        CREATE INDEX IF NOT EXISTS "idx_contact_deleted_55743f" ON "contact" ("deleted_at");

        ALTER TABLE "banner" RENAME TO "banner__old";
        CREATE TABLE "banner" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "content" VARCHAR(255) NOT NULL,
            "note" VARCHAR(255),
            "priority" INT,
            "link_url" VARCHAR(500),
            "click_count" INT NOT NULL DEFAULT 0,
            "is_active" INT NOT NULL DEFAULT 1
        );
        INSERT INTO "banner" ("id", "created_at", "updated_at", "content", "note", "priority", "link_url", "click_count", "is_active")
        SELECT "id", "created_at", "updated_at", "content", "note", NULLIF("priority", 0), "link_url", "click_count", "is_active"
        FROM "banner__old";
        DROP TABLE "banner__old";
        CREATE INDEX IF NOT EXISTS "idx_banner_created_423764" ON "banner" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_banner_updated_d2df13" ON "banner" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_banner_priorit_aabc85" ON "banner" ("priority");
        CREATE INDEX IF NOT EXISTS "idx_banner_click_c_516653" ON "banner" ("click_count");
        CREATE INDEX IF NOT EXISTS "idx_banner_is_acti_40ea0b" ON "banner" ("is_active");

        ALTER TABLE "product" RENAME TO "product__old";
        CREATE TABLE "product" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "category_id" BIGINT NOT NULL,
            "brand_id" BIGINT NOT NULL,
            "name" VARCHAR(100) NOT NULL,
            "product_code" VARCHAR(64),
            "desc" VARCHAR(255),
            "detail_description" JSON NOT NULL,
            "cover_image_key" VARCHAR(500) NOT NULL,
            "image_keys" JSON NOT NULL,
            "video_keys" JSON NOT NULL,
            "click_count" INT NOT NULL DEFAULT 0,
            "status" INT NOT NULL DEFAULT 1,
            "order" INT
        );
        INSERT INTO "product" (
            "id", "created_at", "updated_at", "category_id", "brand_id", "name", "product_code", "desc",
            "detail_description", "cover_image_key", "image_keys", "video_keys", "click_count", "status", "order"
        )
        SELECT
            "id", "created_at", "updated_at", "category_id", "brand_id", "name", "product_code", "desc",
            "detail_description", "cover_image_key", "image_keys", "video_keys", "click_count", "status", NULLIF("order", 0)
        FROM "product__old";
        DROP TABLE "product__old";
        CREATE INDEX IF NOT EXISTS "idx_product_created_9eb6f4" ON "product" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_product_updated_2f7d71" ON "product" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_product_categor_2b519b" ON "product" ("category_id");
        CREATE INDEX IF NOT EXISTS "idx_product_brand_i_fbdc11" ON "product" ("brand_id");
        CREATE INDEX IF NOT EXISTS "idx_product_name_683352" ON "product" ("name");
        CREATE INDEX IF NOT EXISTS "idx_product_product_e35c67" ON "product" ("product_code");
        CREATE INDEX IF NOT EXISTS "idx_product_click_c_abe3fc" ON "product" ("click_count");
        CREATE INDEX IF NOT EXISTS "idx_product_status_cb6e1f" ON "product" ("status");
        CREATE INDEX IF NOT EXISTS "idx_product_order_2e8699" ON "product" ("order");

        PRAGMA foreign_keys=ON;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        PRAGMA foreign_keys=OFF;

        ALTER TABLE "category" RENAME TO "category__old";
        CREATE TABLE "category" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "name" VARCHAR(50) NOT NULL UNIQUE,
            "desc" VARCHAR(255),
            "order" INT NOT NULL DEFAULT 0,
            "is_active" INT NOT NULL DEFAULT 1
        );
        INSERT INTO "category" ("id", "created_at", "updated_at", "name", "desc", "order", "is_active")
        SELECT "id", "created_at", "updated_at", "name", "desc", COALESCE("order", 0), "is_active"
        FROM "category__old";
        DROP TABLE "category__old";
        CREATE INDEX IF NOT EXISTS "idx_category_created_1d8a13" ON "category" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_category_updated_446ede" ON "category" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_category_name_8b0cb9" ON "category" ("name");
        CREATE INDEX IF NOT EXISTS "idx_category_order_ebae39" ON "category" ("order");
        CREATE INDEX IF NOT EXISTS "idx_category_is_acti_16ce8c" ON "category" ("is_active");

        ALTER TABLE "tag" RENAME TO "tag__old";
        CREATE TABLE "tag" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "name" VARCHAR(100) NOT NULL UNIQUE,
            "remark" VARCHAR(255),
            "search_count" INT NOT NULL DEFAULT 0,
            "sort" INT NOT NULL DEFAULT 0,
            "is_active" INT NOT NULL DEFAULT 1
        );
        INSERT INTO "tag" ("id", "created_at", "updated_at", "name", "remark", "search_count", "sort", "is_active")
        SELECT "id", "created_at", "updated_at", "name", "remark", "search_count", COALESCE("sort", 0), "is_active"
        FROM "tag__old";
        DROP TABLE "tag__old";
        CREATE INDEX IF NOT EXISTS "idx_tag_created_e4e466" ON "tag" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_tag_updated_fb661e" ON "tag" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_tag_name_a7b9a6" ON "tag" ("name");
        CREATE INDEX IF NOT EXISTS "idx_tag_search__566698" ON "tag" ("search_count");
        CREATE INDEX IF NOT EXISTS "idx_tag_sort_73ff0f" ON "tag" ("sort");
        CREATE INDEX IF NOT EXISTS "idx_tag_is_acti_50cf59" ON "tag" ("is_active");

        ALTER TABLE "brand" RENAME TO "brand__old";
        CREATE TABLE "brand" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "name" VARCHAR(100) NOT NULL,
            "desc" VARCHAR(255),
            "search_count" INT NOT NULL DEFAULT 0,
            "order" INT NOT NULL DEFAULT 0,
            "is_active" INT NOT NULL DEFAULT 1
        );
        INSERT INTO "brand" ("id", "created_at", "updated_at", "name", "desc", "search_count", "order", "is_active")
        SELECT "id", "created_at", "updated_at", "name", "desc", "search_count", COALESCE("order", 0), "is_active"
        FROM "brand__old";
        DROP TABLE "brand__old";
        CREATE INDEX IF NOT EXISTS "idx_brand_created_882788" ON "brand" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_brand_updated_959589" ON "brand" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_brand_name_c4e2df" ON "brand" ("name");
        CREATE INDEX IF NOT EXISTS "idx_brand_search__39fa28" ON "brand" ("search_count");
        CREATE INDEX IF NOT EXISTS "idx_brand_order_0a0d90" ON "brand" ("order");
        CREATE INDEX IF NOT EXISTS "idx_brand_is_acti_c5b780" ON "brand" ("is_active");

        ALTER TABLE "contact" RENAME TO "contact__old";
        CREATE TABLE "contact" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "platform" VARCHAR(50) NOT NULL,
            "display_name" VARCHAR(100) NOT NULL,
            "contact_type" VARCHAR(30),
            "contact_value" VARCHAR(255),
            "link_url" VARCHAR(500),
            "qr_image_url" VARCHAR(500),
            "order" INT NOT NULL DEFAULT 0,
            "is_active" INT NOT NULL DEFAULT 1,
            "is_deleted" INT NOT NULL DEFAULT 0,
            "deleted_at" TIMESTAMP
        );
        INSERT INTO "contact" (
            "id", "created_at", "updated_at", "platform", "display_name", "contact_type", "contact_value",
            "link_url", "qr_image_url", "order", "is_active", "is_deleted", "deleted_at"
        )
        SELECT
            "id", "created_at", "updated_at", "platform", "display_name", "contact_type", "contact_value",
            "link_url", "qr_image_url", COALESCE("order", 0), "is_active", "is_deleted", "deleted_at"
        FROM "contact__old";
        DROP TABLE "contact__old";
        CREATE INDEX IF NOT EXISTS "idx_contact_created_edee29" ON "contact" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_contact_updated_b40825" ON "contact" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_contact_platfor_0b6de8" ON "contact" ("platform");
        CREATE INDEX IF NOT EXISTS "idx_contact_display_f0b8bd" ON "contact" ("display_name");
        CREATE INDEX IF NOT EXISTS "idx_contact_contact_1715cc" ON "contact" ("contact_type");
        CREATE INDEX IF NOT EXISTS "idx_contact_order_ea68b2" ON "contact" ("order");
        CREATE INDEX IF NOT EXISTS "idx_contact_is_acti_87f467" ON "contact" ("is_active");
        CREATE INDEX IF NOT EXISTS "idx_contact_is_deleted" ON "contact" ("is_deleted");
        CREATE INDEX IF NOT EXISTS "idx_contact_deleted_at" ON "contact" ("deleted_at");
        CREATE INDEX IF NOT EXISTS "idx_contact_is_dele_808a7b" ON "contact" ("is_deleted");
        CREATE INDEX IF NOT EXISTS "idx_contact_deleted_55743f" ON "contact" ("deleted_at");

        ALTER TABLE "banner" RENAME TO "banner__old";
        CREATE TABLE "banner" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "content" VARCHAR(255) NOT NULL,
            "note" VARCHAR(255),
            "priority" INT NOT NULL DEFAULT 0,
            "link_url" VARCHAR(500),
            "click_count" INT NOT NULL DEFAULT 0,
            "is_active" INT NOT NULL DEFAULT 1
        );
        INSERT INTO "banner" ("id", "created_at", "updated_at", "content", "note", "priority", "link_url", "click_count", "is_active")
        SELECT "id", "created_at", "updated_at", "content", "note", COALESCE("priority", 0), "link_url", "click_count", "is_active"
        FROM "banner__old";
        DROP TABLE "banner__old";
        CREATE INDEX IF NOT EXISTS "idx_banner_created_423764" ON "banner" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_banner_updated_d2df13" ON "banner" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_banner_priorit_aabc85" ON "banner" ("priority");
        CREATE INDEX IF NOT EXISTS "idx_banner_click_c_516653" ON "banner" ("click_count");
        CREATE INDEX IF NOT EXISTS "idx_banner_is_acti_40ea0b" ON "banner" ("is_active");

        ALTER TABLE "product" RENAME TO "product__old";
        CREATE TABLE "product" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "category_id" BIGINT NOT NULL,
            "brand_id" BIGINT NOT NULL,
            "name" VARCHAR(100) NOT NULL,
            "product_code" VARCHAR(64),
            "desc" VARCHAR(255),
            "detail_description" JSON NOT NULL,
            "cover_image_key" VARCHAR(500) NOT NULL,
            "image_keys" JSON NOT NULL,
            "video_keys" JSON NOT NULL,
            "click_count" INT NOT NULL DEFAULT 0,
            "status" INT NOT NULL DEFAULT 1,
            "order" INT NOT NULL DEFAULT 0
        );
        INSERT INTO "product" (
            "id", "created_at", "updated_at", "category_id", "brand_id", "name", "product_code", "desc",
            "detail_description", "cover_image_key", "image_keys", "video_keys", "click_count", "status", "order"
        )
        SELECT
            "id", "created_at", "updated_at", "category_id", "brand_id", "name", "product_code", "desc",
            "detail_description", "cover_image_key", "image_keys", "video_keys", "click_count", "status", COALESCE("order", 0)
        FROM "product__old";
        DROP TABLE "product__old";
        CREATE INDEX IF NOT EXISTS "idx_product_created_9eb6f4" ON "product" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_product_updated_2f7d71" ON "product" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_product_categor_2b519b" ON "product" ("category_id");
        CREATE INDEX IF NOT EXISTS "idx_product_brand_i_fbdc11" ON "product" ("brand_id");
        CREATE INDEX IF NOT EXISTS "idx_product_name_683352" ON "product" ("name");
        CREATE INDEX IF NOT EXISTS "idx_product_product_e35c67" ON "product" ("product_code");
        CREATE INDEX IF NOT EXISTS "idx_product_click_c_abe3fc" ON "product" ("click_count");
        CREATE INDEX IF NOT EXISTS "idx_product_status_cb6e1f" ON "product" ("status");
        CREATE INDEX IF NOT EXISTS "idx_product_order_2e8699" ON "product" ("order");

        PRAGMA foreign_keys=ON;
    """
