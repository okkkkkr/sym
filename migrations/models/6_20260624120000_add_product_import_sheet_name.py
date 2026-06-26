from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "product_import_task_item" ADD COLUMN IF NOT EXISTS "sheet_name" VARCHAR(255) NOT NULL DEFAULT '';
        CREATE INDEX IF NOT EXISTS "idx_product_import_task_item_sheet_n_3c40c2" ON "product_import_task_item" ("sheet_name");
        COMMENT ON COLUMN "product_import_task_item"."sheet_name" IS 'Excel工作表名称';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_product_import_task_item_sheet_n_3c40c2";
        ALTER TABLE "product_import_task_item" DROP COLUMN IF EXISTS "sheet_name";
    """
