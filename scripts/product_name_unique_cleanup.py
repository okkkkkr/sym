import argparse
import asyncio
from collections import defaultdict

from tortoise import Tortoise

from app.controllers.product import product_controller
from app.models.admin import Product
from app.settings import settings


def build_dedup_name(name: str, suffix: int) -> str:
    base_name = str(name or "").strip() or "Unnamed Product"
    marker = f" ({suffix})"
    return f"{base_name[: max(0, 100 - len(marker))]}{marker}"


async def collect_duplicates() -> tuple[dict[str, list[Product]], dict[str, list[Product]]]:
    exact_groups: dict[str, list[Product]] = defaultdict(list)
    normalized_groups: dict[str, list[Product]] = defaultdict(list)

    for product in await Product.all().order_by("id"):
        exact_groups[product.name].append(product)
        normalized_groups[product_controller.normalize_name(product.name)].append(product)

    exact_duplicates = {
        name: products
        for name, products in exact_groups.items()
        if name and len(products) > 1
    }
    normalized_duplicates = {
        name: products
        for name, products in normalized_groups.items()
        if name and len(products) > 1
    }
    return exact_duplicates, normalized_duplicates


async def apply_normalized_dedup(normalized_duplicates: dict[str, list[Product]]) -> int:
    renamed_count = 0
    for products in normalized_duplicates.values():
        seen_names = {
            product_controller.normalize_name(product.name): product.id
            for product in await Product.all().order_by("id")
        }
        for index, product in enumerate(products[1:], start=2):
            candidate = build_dedup_name(product.name, index)
            while product_controller.normalize_name(candidate) in seen_names:
                index += 1
                candidate = build_dedup_name(product.name, index)
            product.name = candidate
            await product.save(update_fields=["name"])
            seen_names[product_controller.normalize_name(candidate)] = product.id
            renamed_count += 1
    return renamed_count


async def main(apply_changes: bool) -> None:
    await Tortoise.init(config=settings.TORTOISE_ORM)
    try:
        exact_duplicates, normalized_duplicates = await collect_duplicates()

        if not exact_duplicates and not normalized_duplicates:
            print("No duplicate product names found.")
            return

        if exact_duplicates:
            print("Exact duplicates:")
            for name, products in exact_duplicates.items():
                print(f"  {name}: {[product.id for product in products]}")

        if normalized_duplicates:
            print("Normalized duplicates:")
            for normalized_name, products in normalized_duplicates.items():
                print(
                    f"  {normalized_name}: "
                    f"{[(product.id, product.name) for product in products]}"
                )

        if not apply_changes:
            print("Dry run only. Re-run with --apply to rename later duplicates.")
            return

        renamed_count = await apply_normalized_dedup(normalized_duplicates)
        print(f"Renamed {renamed_count} product names.")
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit or clean duplicate product names.")
    parser.add_argument("--apply", action="store_true", help="Rename later duplicates in place.")
    args = parser.parse_args()
    asyncio.run(main(apply_changes=args.apply))
