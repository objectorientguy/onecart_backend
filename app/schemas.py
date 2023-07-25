from typing import List
from pydantic import BaseModel
from datetime import date


class UserData(BaseModel):
    customer_id: str
    customer_name: str | None = None
    customer_contact: int
    customer_birthdate: date | None = None
    companies: List[str] | None = None

    class Config:
        from_attributes = True


class Address(BaseModel):
    address_id: int | None = None
    user_contact: int
    address_title: str
    address_name: str
    city: str
    pincode: int
    company: str | None = None

    class Config:
        from_attributes = True


class AddAddress(Address):
    pass
