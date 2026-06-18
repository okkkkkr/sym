from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "certificate_status"
        ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at" AT TIME ZONE 'Asia/Shanghai',
        ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at" AT TIME ZONE 'Asia/Shanghai',
        ALTER COLUMN "not_before" TYPE TIMESTAMPTZ USING "not_before" AT TIME ZONE 'Asia/Shanghai',
        ALTER COLUMN "not_after" TYPE TIMESTAMPTZ USING "not_after" AT TIME ZONE 'Asia/Shanghai',
        ALTER COLUMN "last_checked_at" TYPE TIMESTAMPTZ USING "last_checked_at" AT TIME ZONE 'Asia/Shanghai';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "certificate_status"
        ALTER COLUMN "created_at" TYPE TIMESTAMP USING "created_at" AT TIME ZONE 'Asia/Shanghai',
        ALTER COLUMN "updated_at" TYPE TIMESTAMP USING "updated_at" AT TIME ZONE 'Asia/Shanghai',
        ALTER COLUMN "not_before" TYPE TIMESTAMP USING "not_before" AT TIME ZONE 'Asia/Shanghai',
        ALTER COLUMN "not_after" TYPE TIMESTAMP USING "not_after" AT TIME ZONE 'Asia/Shanghai',
        ALTER COLUMN "last_checked_at" TYPE TIMESTAMP USING "last_checked_at" AT TIME ZONE 'Asia/Shanghai';
    """
