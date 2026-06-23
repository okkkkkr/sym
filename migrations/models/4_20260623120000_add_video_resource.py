from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "video_resource" (
            "id" BIGSERIAL NOT NULL PRIMARY KEY,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
            "original_file_name" VARCHAR(255) NOT NULL,
            "original_file_path" VARCHAR(500) NOT NULL,
            "compressed_file_path" VARCHAR(500),
            "product_id" BIGINT,
            "update_plan_id" BIGINT,
            "storage_provider" VARCHAR(50) NOT NULL DEFAULT '',
            "storage_key" VARCHAR(500) NOT NULL DEFAULT '',
            "public_url" VARCHAR(500) NOT NULL DEFAULT '',
            "original_size" BIGINT NOT NULL DEFAULT 0,
            "compressed_size" BIGINT,
            "error_message" TEXT,
            "created_by" BIGINT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_video_resource_created_dfb61d" ON "video_resource" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_video_resource_updated_f04811" ON "video_resource" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_video_resource_status_9d14ac" ON "video_resource" ("status");
        CREATE INDEX IF NOT EXISTS "idx_video_resource_created_22cc46" ON "video_resource" ("created_by");
        CREATE INDEX IF NOT EXISTS "idx_video_resource_product_53df4c" ON "video_resource" ("product_id");
        CREATE INDEX IF NOT EXISTS "idx_video_resource_update__1d89dd" ON "video_resource" ("update_plan_id");
        COMMENT ON COLUMN "video_resource"."status" IS '处理状态';
        COMMENT ON COLUMN "video_resource"."original_file_name" IS '原始文件名';
        COMMENT ON COLUMN "video_resource"."original_file_path" IS '原始临时文件路径';
        COMMENT ON COLUMN "video_resource"."compressed_file_path" IS '压缩后临时文件路径';
        COMMENT ON COLUMN "video_resource"."product_id" IS '关联好物ID';
        COMMENT ON COLUMN "video_resource"."update_plan_id" IS '视频更新计划ID';
        COMMENT ON COLUMN "video_resource"."storage_provider" IS '存储驱动';
        COMMENT ON COLUMN "video_resource"."storage_key" IS '对象 Key';
        COMMENT ON COLUMN "video_resource"."public_url" IS '公开访问地址';
        COMMENT ON COLUMN "video_resource"."original_size" IS '原始文件大小';
        COMMENT ON COLUMN "video_resource"."compressed_size" IS '压缩后文件大小';
        COMMENT ON COLUMN "video_resource"."error_message" IS '错误信息';
        COMMENT ON COLUMN "video_resource"."created_by" IS '上传人ID';
        CREATE TABLE IF NOT EXISTS "product_video_update_plan" (
            "id" BIGSERIAL NOT NULL PRIMARY KEY,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "product_id" BIGINT NOT NULL,
            "status" VARCHAR(20) NOT NULL DEFAULT 'active',
            "items" JSONB NOT NULL,
            "previous_video_keys" JSONB NOT NULL,
            "created_by" BIGINT NOT NULL,
            "error_message" TEXT
        );
        CREATE INDEX IF NOT EXISTS "idx_product_video_update_plan_created_2aa1ae" ON "product_video_update_plan" ("created_at");
        CREATE INDEX IF NOT EXISTS "idx_product_video_update_plan_updated_f78773" ON "product_video_update_plan" ("updated_at");
        CREATE INDEX IF NOT EXISTS "idx_product_video_update_plan_product_955f80" ON "product_video_update_plan" ("product_id");
        CREATE INDEX IF NOT EXISTS "idx_product_video_update_plan_status_2fda23" ON "product_video_update_plan" ("status");
        CREATE INDEX IF NOT EXISTS "idx_product_video_update_plan_created_b11db5" ON "product_video_update_plan" ("created_by");
        COMMENT ON COLUMN "product_video_update_plan"."product_id" IS '好物ID';
        COMMENT ON COLUMN "product_video_update_plan"."status" IS '计划状态';
        COMMENT ON COLUMN "product_video_update_plan"."items" IS '视频条目序列';
        COMMENT ON COLUMN "product_video_update_plan"."previous_video_keys" IS '保存前视频 Key 列表';
        COMMENT ON COLUMN "product_video_update_plan"."created_by" IS '创建人ID';
        COMMENT ON COLUMN "product_video_update_plan"."error_message" IS '错误信息';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "product_video_update_plan";
        DROP TABLE IF EXISTS "video_resource";
    """
