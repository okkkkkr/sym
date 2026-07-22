from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "token_version" INT NOT NULL DEFAULT 0;
        COMMENT ON COLUMN "user"."token_version" IS '令牌撤销版本';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return 'ALTER TABLE "user" DROP COLUMN "token_version";'
