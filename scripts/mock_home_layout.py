import argparse
import asyncio

from tortoise import Tortoise

from app.controllers.home_layout import home_layout_controller
from app.schemas.home_layouts import HomeLayoutDraftSaveIn
from app.settings import settings


def build_mock_payload() -> dict:
    return {
        "page_code": "home",
        "modules": [
            {
                "type": "single_image",
                "sort": 1,
                "is_enabled": True,
                "title": "The perfect start",
                "action": {
                    "text": "Morning collection",
                    "link": "/sym",
                    "target": "self",
                },
                "config": {
                    "ratio": "16:7",
                    "text_position": "center",
                    "overlay": True,
                },
                "items": [
                    {
                        "sort": 1,
                        "image": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1600&q=80",
                        "title": "Morning Rituals",
                        "description": "A calm entry banner for the storefront homepage.",
                        "badge": "",
                        "action": {
                            "text": "Shop now",
                            "link": "/sym",
                            "target": "self",
                        },
                    }
                ],
            },
            {
                "type": "grid_4",
                "sort": 2,
                "is_enabled": True,
                "title": "Best Sellers",
                "action": {
                    "text": "Shop range",
                    "link": "/sym",
                    "target": "self",
                },
                "config": {},
                "items": [
                    {
                        "sort": 1,
                        "image": "https://images.unsplash.com/photo-1464306076886-da185f6a9d05?auto=format&fit=crop&w=900&q=80",
                        "title": "First harvest",
                        "description": "Wabi-sabi Ice Tea",
                        "badge": "",
                        "action": {"text": "View", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 2,
                        "image": "https://images.unsplash.com/photo-1515823064-d6e0c04616a7?auto=format&fit=crop&w=900&q=80",
                        "title": "Stone ground",
                        "description": "Natsukashii Matcha Tea",
                        "badge": "",
                        "action": {"text": "View", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 3,
                        "image": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&q=80",
                        "title": "Amber roast",
                        "description": "Organic Mamori Tai",
                        "badge": "Sale",
                        "action": {"text": "View", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 4,
                        "image": "https://images.unsplash.com/photo-1470337458703-46ad1756a187?auto=format&fit=crop&w=900&q=80",
                        "title": "Fresh canopy",
                        "description": "Furusato Green Tea",
                        "badge": "",
                        "action": {"text": "View", "link": "/sym", "target": "self"},
                    },
                ],
            },
            {
                "type": "grid_2",
                "sort": 3,
                "is_enabled": True,
                "title": "Upcoming arrivals",
                "action": {
                    "text": "New in store",
                    "link": "/sym",
                    "target": "self",
                },
                "config": {},
                "items": [
                    {
                        "sort": 1,
                        "image": "https://images.unsplash.com/photo-1515823662972-da6a2e4d3002?auto=format&fit=crop&w=1200&q=80",
                        "title": "Shop now",
                        "description": "Herbal Tea",
                        "badge": "",
                        "action": {"text": "Shop now", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 2,
                        "image": "https://images.unsplash.com/photo-1558160074-4d7d8bdf4256?auto=format&fit=crop&w=1200&q=80",
                        "title": "Shop now",
                        "description": "Medicinal Tea",
                        "badge": "",
                        "action": {"text": "Shop now", "link": "/sym", "target": "self"},
                    },
                ],
            },
            {
                "type": "grid_8",
                "sort": 4,
                "is_enabled": True,
                "title": "Shop by mood",
                "action": {
                    "text": "Explore all",
                    "link": "/sym",
                    "target": "self",
                },
                "config": {},
                "items": [
                    {"sort": 1, "image": "https://images.unsplash.com/photo-1464306076886-da185f6a9d05?auto=format&fit=crop&w=600&q=80", "title": "Quiet mornings", "description": "Soft brew", "badge": "", "action": {"text": "", "link": "/sym", "target": "self"}},
                    {"sort": 2, "image": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=600&q=80", "title": "Creative desk", "description": "Focus tea", "badge": "", "action": {"text": "", "link": "/sym", "target": "self"}},
                    {"sort": 3, "image": "https://images.unsplash.com/photo-1459755486867-b55449bb39ff?auto=format&fit=crop&w=600&q=80", "title": "Weekend calm", "description": "Slow steep", "badge": "", "action": {"text": "", "link": "/sym", "target": "self"}},
                    {"sort": 4, "image": "https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=600&q=80", "title": "Green brightness", "description": "Fresh note", "badge": "", "action": {"text": "", "link": "/sym", "target": "self"}},
                    {"sort": 5, "image": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=600&q=80", "title": "Midday reset", "description": "Warm cup", "badge": "", "action": {"text": "", "link": "/sym", "target": "self"}},
                    {"sort": 6, "image": "https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=600&q=80", "title": "After dinner", "description": "Herbal ease", "badge": "", "action": {"text": "", "link": "/sym", "target": "self"}},
                    {"sort": 7, "image": "https://images.unsplash.com/photo-1481391032119-d89fee407e44?auto=format&fit=crop&w=600&q=80", "title": "Gift picks", "description": "Shared sets", "badge": "", "action": {"text": "", "link": "/sym", "target": "self"}},
                    {"sort": 8, "image": "https://images.unsplash.com/photo-1466306076886-da185f6a9d05?auto=format&fit=crop&w=600&q=80", "title": "Signature jars", "description": "Shelf icons", "badge": "", "action": {"text": "", "link": "/sym", "target": "self"}},
                ],
            },
            {
                "type": "carousel",
                "sort": 5,
                "is_enabled": True,
                "title": "Seasonal stories",
                "action": {
                    "text": "Browse stories",
                    "link": "/sym",
                    "target": "self",
                },
                "config": {
                    "autoplay": True,
                    "interval": 3200,
                    "show_dots": True,
                },
                "items": [
                    {
                        "sort": 1,
                        "image": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1600&q=80",
                        "title": "Clay pot rituals",
                        "description": "A rich carousel slide for traditional tea sets.",
                        "badge": "Featured",
                        "action": {"text": "Discover", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 2,
                        "image": "https://images.unsplash.com/photo-1507914372368-b2b085b925a1?auto=format&fit=crop&w=1600&q=80",
                        "title": "Spring harvest",
                        "description": "Bright leaves and quiet details for a fresh homepage state.",
                        "badge": "New",
                        "action": {"text": "See more", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 3,
                        "image": "https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=1600&q=80",
                        "title": "Evening steep",
                        "description": "Warm amber notes and a relaxed product story.",
                        "badge": "",
                        "action": {"text": "Open", "link": "/sym", "target": "self"},
                    },
                ],
            },
            {
                "type": "horizontal_list",
                "sort": 6,
                "is_enabled": True,
                "title": "Editor picks",
                "action": {
                    "text": "Scroll through",
                    "link": "/sym",
                    "target": "self",
                },
                "config": {},
                "items": [
                    {
                        "sort": 1,
                        "image": "https://images.unsplash.com/photo-1459755486867-b55449bb39ff?auto=format&fit=crop&w=900&q=80",
                        "title": "Citrus aroma",
                        "description": "Bright leaf",
                        "badge": "Hot",
                        "action": {"text": "Read more", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 2,
                        "image": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=80",
                        "title": "Wood tray set",
                        "description": "Tabletop calm",
                        "badge": "",
                        "action": {"text": "Read more", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 3,
                        "image": "https://images.unsplash.com/photo-1481391032119-d89fee407e44?auto=format&fit=crop&w=900&q=80",
                        "title": "Minimal gifting",
                        "description": "Bundle idea",
                        "badge": "",
                        "action": {"text": "Read more", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 4,
                        "image": "https://images.unsplash.com/photo-1515823662972-da6a2e4d3002?auto=format&fit=crop&w=900&q=80",
                        "title": "Glass pitcher",
                        "description": "Clear brew",
                        "badge": "New",
                        "action": {"text": "Read more", "link": "/sym", "target": "self"},
                    },
                    {
                        "sort": 5,
                        "image": "https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=900&q=80",
                        "title": "Dark roast notes",
                        "description": "Deep cup",
                        "badge": "",
                        "action": {"text": "Read more", "link": "/sym", "target": "self"},
                    },
                ],
            },
        ],
    }


async def main(apply_publish: bool) -> None:
    await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
    try:
        payload = HomeLayoutDraftSaveIn(**build_mock_payload())
        await home_layout_controller.save_draft(payload)
        print("Home layout draft saved.")
        if apply_publish:
            published = await home_layout_controller.publish("home")
            print(
                "Home layout published.",
                f"version={published['version']}",
                f"modules={len(published['modules'])}",
            )
        else:
            print("Dry run finished. Re-run with --publish to publish the draft.")
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed mock home layout data.")
    parser.add_argument("--publish", action="store_true", help="Publish the generated home layout after saving draft.")
    args = parser.parse_args()
    asyncio.run(main(apply_publish=args.publish))
