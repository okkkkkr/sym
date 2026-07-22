from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "media_upload" (
            "id" BIGSERIAL NOT NULL PRIMARY KEY,
            "object_key" VARCHAR(500) NOT NULL UNIQUE,
            "uploaded_by" INT NOT NULL,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        COMMENT ON COLUMN "media_upload"."object_key" IS '上传对象 Key';
        COMMENT ON COLUMN "media_upload"."uploaded_by" IS '上传用户 ID';
        CREATE INDEX IF NOT EXISTS "idx_media_upload_created_6cb532" ON "media_upload" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_media_upload_updated_e655af" ON "media_upload" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_media_up_object__169069" ON "media_upload" ("object_key");
        CREATE INDEX IF NOT EXISTS "idx_media_up_uploade_47eac1" ON "media_upload" ("uploaded_by");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return 'DROP TABLE IF EXISTS "media_upload";'
