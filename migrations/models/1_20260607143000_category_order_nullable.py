from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "category" ALTER COLUMN "order" DROP NOT NULL;
        ALTER TABLE "category" ALTER COLUMN "order" DROP DEFAULT;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        UPDATE "category" SET "order" = 0 WHERE "order" IS NULL;
        ALTER TABLE "category" ALTER COLUMN "order" SET DEFAULT 0;
        ALTER TABLE "category" ALTER COLUMN "order" SET NOT NULL;
    """
