from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "certificate_status" (
            "id" BIGSERIAL NOT NULL PRIMARY KEY,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "code" VARCHAR(50) NOT NULL UNIQUE,
            "display_name" VARCHAR(100) NOT NULL DEFAULT '',
            "domain" VARCHAR(255) NOT NULL DEFAULT '',
            "cert_path" VARCHAR(500) NOT NULL DEFAULT '',
            "status" VARCHAR(20) NOT NULL DEFAULT 'error',
            "not_before" TIMESTAMP,
            "not_after" TIMESTAMP,
            "days_remaining" INT,
            "last_checked_at" TIMESTAMP,
            "last_error" VARCHAR(500) NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS "idx_certificate_status_code_4e6061" ON "certificate_status" ("code");
        CREATE INDEX IF NOT EXISTS "idx_certificate_status_status_8fb676" ON "certificate_status" ("status");
        CREATE INDEX IF NOT EXISTS "idx_certificate_status_not_bef_47307b" ON "certificate_status" ("not_before");
        CREATE INDEX IF NOT EXISTS "idx_certificate_status_not_aft_2d1678" ON "certificate_status" ("not_after");
        CREATE INDEX IF NOT EXISTS "idx_certificate_status_days_re_948864" ON "certificate_status" ("days_remaining");
        CREATE INDEX IF NOT EXISTS "idx_certificate_status_last_ch_09dff8" ON "certificate_status" ("last_checked_at");
        CREATE INDEX IF NOT EXISTS "idx_certificate_status_created_70bb71" ON "certificate_status" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_certificate_status_updated_4caa45" ON "certificate_status" ("updated_at");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "certificate_status";
    """
