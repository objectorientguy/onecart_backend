from typing import Optional
from pydantic import BaseModel
from datetime import date


class User(BaseModel):
    customer_id: str
    customer_name: Optional[str]
    customer_contact: int
    customer_birthdate: Optional[date]
    is_new_customer: Optional[bool]

    class Config:
        orm_mode = True


