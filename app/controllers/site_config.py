from app.core.crud import CRUDBase
from app.models.admin import SiteConfig
from app.schemas.site_configs import SiteConfigUpdate


def serialize_site_config(site_config_obj: SiteConfig | None) -> dict:
    if not site_config_obj:
        return {
            "logo_url": "",
            "about_title": "",
            "about_lines": [],
            "footer_disclaimer": "",
            "share_base_url": "",
        }

    return {
        "logo_url": str(site_config_obj.logo_url or "").strip(),
        "about_title": str(site_config_obj.about_title or "").strip(),
        "about_lines": [str(item).strip() for item in site_config_obj.about_lines or [] if str(item).strip()],
        "footer_disclaimer": str(site_config_obj.footer_disclaimer or "").strip(),
        "share_base_url": str(site_config_obj.share_base_url or "").strip(),
    }


class SiteConfigController(CRUDBase[SiteConfig, SiteConfigUpdate, SiteConfigUpdate]):
    def __init__(self):
        super().__init__(model=SiteConfig)

    async def get_singleton(self) -> SiteConfig | None:
        return await self.model.all().order_by("id").first()

    async def update_singleton(self, obj_in: SiteConfigUpdate) -> SiteConfig:
        site_config_obj = await self.get_singleton()
        payload = obj_in.model_dump()
        if site_config_obj:
            site_config_obj.update_from_dict(payload)
            await site_config_obj.save()
            return site_config_obj
        return await self.model.create(**payload)


site_config_controller = SiteConfigController()
