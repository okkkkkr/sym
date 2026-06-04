from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "home_layout"
        ADD COLUMN "common_config" JSON NOT NULL DEFAULT '{"show_banner": true, "show_navigation": true, "show_footer": true}';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "home_layout" DROP COLUMN "common_config";
    """
