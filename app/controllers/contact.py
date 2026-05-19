from app.core.crud import CRUDBase
from app.models.admin import Contact
from app.schemas.contacts import ContactCreate, ContactUpdate


class ContactController(CRUDBase[Contact, ContactCreate, ContactUpdate]):
    def __init__(self):
        super().__init__(model=Contact)


contact_controller = ContactController()