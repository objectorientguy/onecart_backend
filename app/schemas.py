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
    address_type: str
    address_name: str
    city: str
    pincode: int

    class Config:
        from_attributes = True


class AddAddress(Address):
    pass


class CartItemCreate(BaseModel):
    product_id: int


class CartCreate(BaseModel):
    company_id: int
    user_id: int
    items: List[CartItemCreate]


class CartItemResponse(BaseModel):
    id: int
    product_id: int


class CartResponse(BaseModel):
    id: int
    company_id: int
    user_id: int
    items: List[CartItemResponse]


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
