from app.core.crud import CRUDBase
from app.models.admin import SiteConfig
from app.schemas.site_configs import SiteConfigUpdate
from app.services.media_cleanup import delete_media_keys
from app.services.media_storage import media_storage_service


def serialize_site_config(
    site_config_obj: SiteConfig | None, include_storage: bool = False, include_key: bool = False
) -> dict:
    if not site_config_obj:
        data = {
            "logo_url": "",
            "about_title": "",
            "about_lines": [],
            "footer_disclaimer": "",
            "share_base_url": "",
        }
        if include_key:
            data["logo_key"] = ""
        return data

    logo_key = str(site_config_obj.logo_key or "").strip()
    data = {
        "logo_url": media_storage_service.serialize_object_key(logo_key),
        "about_title": str(site_config_obj.about_title or "").strip(),
        "about_lines": [str(item).strip() for item in site_config_obj.about_lines or [] if str(item).strip()],
        "footer_disclaimer": str(site_config_obj.footer_disclaimer or "").strip(),
        "share_base_url": str(site_config_obj.share_base_url or "").strip(),
    }
    if include_key:
        data["logo_key"] = logo_key
    return data


class SiteConfigController(CRUDBase[SiteConfig, SiteConfigUpdate, SiteConfigUpdate]):
    def __init__(self):
        super().__init__(model=SiteConfig)

    async def get_singleton(self) -> SiteConfig | None:
        return await self.model.all().order_by("id").first()

    async def update_singleton(self, obj_in: SiteConfigUpdate) -> SiteConfig:
        site_config_obj = await self.get_singleton()
        payload = obj_in.model_dump()
        previous_logo_key = str(site_config_obj.logo_key or "").strip() if site_config_obj else ""
        if site_config_obj:
            site_config_obj.update_from_dict(payload)
            await site_config_obj.save()
        else:
            site_config_obj = await self.model.create(**payload)

        logo_key = str(site_config_obj.logo_key or "").strip()
        await self.delete_logo_file(previous_logo_key, exclude_logo_key=logo_key)
        return site_config_obj

    async def delete_logo_file(self, logo_key: str, exclude_logo_key: str = "") -> None:
        normalized_logo_key = str(logo_key or "").strip()
        if not normalized_logo_key or normalized_logo_key == str(exclude_logo_key or "").strip():
            return
        await delete_media_keys([normalized_logo_key])


site_config_controller = SiteConfigController()
