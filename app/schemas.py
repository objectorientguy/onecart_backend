from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import date, time, datetime


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

class Shop(BaseModel):
    shop_name: str
    shop_description: str
    shop_image: str
    shop_contact: int
    shop_address: str
    shop_coordinates: str
    shop_mok: str
    shop_service: str
    is_available: bool
    company_name: str


class Category(BaseModel):
    category_id: Optional[int] | None = None
    category_name: str
    category_image: str

    class Config:
        from_attributes = True


class EditCategory(Category):
    pass

class ProductCategory(BaseModel):
    product_id: int
    category_id: int


    class Config:
        from_attributes = True

class Product(BaseModel):
    product_id: int | None = None
    brand_id: int
    product_name: str
    details: str
    tags: str


    class Config:
        from_attributes = True

class ProductVariant(BaseModel):
    variant_id: Optional[int] | None = None
    variant_cost: float
    count: int
    brand_name: str
    discounted_cost: float
    discount: int
    quantity: str
    description: str
    discounted_cost: float
    image: List[str]
    ratings: int
    product_id: int

    class Config:
        from_attributes = True


class EditProduct(Product):
    pass


class UserData(BaseModel):
    customer_id: str
    customer_name: str | None = None
    customer_contact: int
    customer_birthdate: date | None = None
    email_id: EmailStr
    wallet: float
    prev_pay_mode: str


class EditUserData(UserData):
    customer_name: str | None = None
    customer_contact: int
    customer_birthdate: date | None = None
    email_id: EmailStr
    pass

    class Config:
        from_attributes = True


class Address(BaseModel):
    address_id: int | None = None
    user_contact: int
    address_type: str | None = "Home"
    address_name: str
    phone_no: int
    city: str
    state: str
    pincode: int
    name: str

    class Config:
        from_attributes = True


class AddAddress(Address):
    address_name: str
    address_type: str
    phone_no: int
    city: str
    state: str
    pincode: int

    class Config:
        from_attributes = True


class EditAddress(Address):
    address_name: str
    address_type: str
    phone_no: int
    city: str
    state: str
    pincode: int

    class Config:
        from_attributes = True

# class OrderItems(BaseModel):
#     product_id: int
#     variant: int
#
#     class Config:
#         from_attributes = True

class CartItem(BaseModel):
    cart_id: int
    product_id: int
    variant_id: int
    count: int

    class Config:
        from_attributes = True

class CartSchema(BaseModel):
    # id: int
    company_id: int
    customer_contact: int
    coupon_id: int
    products: str
    # creation_time: datetime

    class Config:
        from_attributes = True


class CompanyLogin(BaseModel):
    email: str
    password: str


class Banners(BaseModel):
    banner_id: int
    description: str
    banner_image: List[str]
    discount: str
    isActive: bool
    tAc: str


class Bookings(BaseModel):
    order_id: int | None = None
    cart_id: int | None = None
    user_contact: int
    address_id: int
    # item_count: int
    # order_placed: datetime | None = None
    # order_confirmation: datetime | None = None
    # order_shipped: datetime | None = None
    # total_price: str
    # payment_type: str
    # products: List[OrderItems]
    order_number: str
    order_date: date
    product_total: float
    order_amount: float
    delivery_fees: float
    invoice_number: str
    invoice_amount: float
    products: List[str]


    class Config:
        from_attributes = True


class BookingsCreate(Bookings):
    pass


class Coupons(BaseModel):
    coupon_id: int
    coupon_image: str
    coupon_name: str
    discount_amount: float
    isActive: bool
    description: str


class CheckoutScreen(BaseModel):
    bill_details: int
    cart_total: float
    discount: float
    coupon_applied: str
    delivery_charges: float = 45.50
    total_bill: float


class Brand(BaseModel):
    brand_id: int
    brand_name: str
    brand_image: str

class Deals(BaseModel):
    shop_id: int
    product_id: int
    deal_name: str
    deal_type: str
    deal_description: str
    deal_discount: int
    deal_start: str
    deal_end: str

# class ShopASSociation(BaseModel):
#
#     product_id: int
#     variant_id: int
#     shop_id: int

class Feature(BaseModel):
    shop_id: int
    feature_image: List[str]

class Speech(BaseModel):
    speech_id: int
    voice_text: str