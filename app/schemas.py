from typing import List, Optional
from pydantic import BaseModel
from datetime import date, time


class UserData(BaseModel):
    customer_id: str
    customer_name: Optional[str]
    customer_contact: int
    customer_birthdate: Optional[date]
    companies: Optional[List[str]]

    class Config:
        from_attributes = True


class Address(BaseModel):
    address_id: Optional[int]
    user_contact: int
    address_title: str
    address_name: str
    city: str
    pincode: int
    company: str

    class Config:
        from_attributes = True


class AddAddress(Address):
    pass


class Cart(BaseModel):
    cart_id: Optional[int]
    user_contact: int
    company_id: str
    products: List[str]

    class Config:
        from_attributes = True


class UpdateCart(Cart):
    pass


class Bookings(BaseModel):
    booking_id: Optional[int]
    user_contact: int
    company_id: str
    products: List[str]
    address_id: int
    booking_time: time
    booking_date: date
    total: str
    coupon: str
    coupon_discount: str

    class Config:
        from_attributes = True
