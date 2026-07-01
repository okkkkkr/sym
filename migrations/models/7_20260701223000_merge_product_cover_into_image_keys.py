from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        UPDATE "product"
        SET "image_keys" = CASE
            WHEN COALESCE("cover_image_key", '') = '' THEN COALESCE("image_keys", '[]'::jsonb)
            WHEN "image_keys" IS NULL OR jsonb_typeof("image_keys") <> 'array' THEN jsonb_build_array("cover_image_key")
            WHEN "image_keys" ? "cover_image_key" THEN "image_keys"
            ELSE "image_keys" || jsonb_build_array("cover_image_key")
        END;
        COMMENT ON COLUMN "product"."cover_image_key" IS '封面图对象 Key，必须来自图片对象 Key 列表';
        COMMENT ON COLUMN "product"."image_keys" IS '图片对象 Key 列表，包含封面图';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        UPDATE "product"
        SET "image_keys" = COALESCE(
            (
                SELECT jsonb_agg("keys"."image_key" ORDER BY "keys"."ordinal")
                FROM jsonb_array_elements_text(COALESCE("product"."image_keys", '[]'::jsonb))
                    WITH ORDINALITY AS "keys"("image_key", "ordinal")
                WHERE "keys"."image_key" <> COALESCE("product"."cover_image_key", '')
            ),
            '[]'::jsonb
        );
        COMMENT ON COLUMN "product"."cover_image_key" IS '封面图对象 Key';
        COMMENT ON COLUMN "product"."image_keys" IS '图片对象 Key 列表';
    """
