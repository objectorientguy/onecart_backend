from typing import List, Optional
from pydantic import BaseModel
from datetime import date, time


class Companies(BaseModel):
    company_id: int | None = None
    user_contact: int
    company_name: str
    password: str
    email: str
    company_contact: int
    company_address: str

    class Config:
        from_attributes = True


class UserCompany(BaseModel):
    company_name: str
    user_contact: int

    class Config:
        from_attributes = True


class Category(BaseModel):
    category_id: Optional[int] | None = None
    category_name: str
    category_image: str

    class Config:
        from_attributes = True


class EditCategory(Category):
    pass


class Product(BaseModel):
    product_id: int | None = None
    company_id: int
    company_name: str
    store_id: int | None = None
    product_name: str
    image: List[str]
    item_count: int
    variants: List[str]
    cost: str
    discounted_cost: int
    details: str


class UserData(BaseModel):
    customer_id: str
    customer_name: str | None = None
    customer_contact: int
    customer_birthdate: date | None = None

    class Config:
        from_attributes = True


class Address(BaseModel):
    address_id: int | None = None
    user_contact: int
    address_title: str
    address_name: str
    city: str
    pincode: int
    company_id: int

    class Config:
        from_attributes = True


class AddAddress(Address):
    pass


class Bookings(BaseModel):
    booking_id: int | None = None
    user_contact: int
    company_name: str
    products: List[Product]
    address_id: int
    booking_time: time
    booking_date: date
    total: str
    coupon: str
    coupon_discount: str

    class Config:
        from_attributes = True


class CompanyLogin(BaseModel):
    email: str
    password: str


class CartSchema(BaseModel):
    id: int
    company_id: int
    customer_contact: int
    #creation_time: datetime


class CartItemSchema(BaseModel):
    id: int
    product_id: int
    cart_id: int
    quantity: int
