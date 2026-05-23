from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    duplicates = await db.execute_query_dict(
        """
        SELECT "name", COUNT(*) AS "count"
        FROM "product"
        GROUP BY "name"
        HAVING COUNT(*) > 1
        ORDER BY "name"
        LIMIT 10
        """
    )
    if duplicates:
        sample = ", ".join(item["name"] for item in duplicates)
        raise RuntimeError(f'Cannot add unique index on product.name because duplicates exist: {sample}')

    return """
        CREATE UNIQUE INDEX IF NOT EXISTS "uidx_product_name" ON "product" ("name");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uidx_product_name";
    """
