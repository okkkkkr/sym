from datetime import datetime, timezone

from app.core.crud import CRUDBase
from app.models.admin import Contact
from app.services.product_media_upload import product_media_upload_service
from app.schemas.contacts import ContactCreate, ContactUpdate


class ContactController(CRUDBase[Contact, ContactCreate, ContactUpdate]):
    def __init__(self):
        super().__init__(model=Contact)

    async def remove(self, id: int) -> None:
        contact_obj = await self.get(id=id)
        contact_obj.is_active = False
        contact_obj.is_deleted = True
        contact_obj.deleted_at = datetime.now(timezone.utc)
        await contact_obj.save(update_fields=["is_active", "is_deleted", "deleted_at"])

    async def serialize(self, contact_obj: Contact, include_preview: bool = False) -> dict:
        data = await contact_obj.to_dict()
        preview_url = product_media_upload_service.serialize_object_key(data.get("qr_image_url"))
        if include_preview:
            data["qr_image_preview_url"] = preview_url
            return data
        data["qr_image_url"] = preview_url
        return data


contact_controller = ContactController()
