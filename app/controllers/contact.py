from datetime import datetime, timezone

from app.core.crud import CRUDBase
from app.models.admin import Contact
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


contact_controller = ContactController()
