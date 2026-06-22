from datetime import datetime, timezone

from app.core.crud import CRUDBase
from app.models.admin import Contact
from app.services.media_cleanup import delete_media_keys, diff_removed_media_keys, normalize_media_key
from app.services.media_storage import media_storage_service
from app.schemas.contacts import ContactCreate, ContactUpdate


class ContactController(CRUDBase[Contact, ContactCreate, ContactUpdate]):
    def __init__(self):
        super().__init__(model=Contact)

    async def remove(self, id: int) -> None:
        contact_obj = await self.get(id=id)
        qr_image_key = normalize_media_key(contact_obj.qr_image_url)
        contact_obj.is_active = False
        contact_obj.is_deleted = True
        contact_obj.deleted_at = datetime.now(timezone.utc)
        await contact_obj.save(update_fields=["is_active", "is_deleted", "deleted_at"])
        await delete_media_keys([qr_image_key])

    async def update(self, id: int, obj_in) -> Contact:
        contact_obj = await self.get(id=id)
        removed_keys = diff_removed_media_keys(
            [contact_obj.qr_image_url],
            [obj_in.get("qr_image_url") if isinstance(obj_in, dict) else obj_in.qr_image_url],
        )
        updated_contact = await super().update(id=id, obj_in=obj_in)
        await delete_media_keys(removed_keys)
        return updated_contact

    async def serialize(self, contact_obj: Contact, include_preview: bool = False) -> dict:
        data = await contact_obj.to_dict()
        preview_url = media_storage_service.serialize_object_key(data.get("qr_image_url"))
        if include_preview:
            data["qr_image_preview_url"] = preview_url
            return data
        data["qr_image_url"] = preview_url
        return data


contact_controller = ContactController()
