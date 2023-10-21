from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import date, time, datetime


class Companies(BaseModel):
    company_id: int | None = None
    company_name: str
    company_domain: str
    company_logo: str
    password: str
    email: str
    services: str
    contact_number: int
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

    class Config:
        from_attributes = True


class ProductVariant(BaseModel):
    variant_id: Optional[int] | None = None
    variant_cost: float
    unit: str
    brand_name: str
    discounted_cost: float
    discount: int | None = None
    quantity: int
    description: str
    discounted_cost: float
    image: List[str]
    ratings: int | None = None
    product_id: int

    class Config:
        from_attributes = True


class EditProduct(Product):
    pass


class UserData(BaseModel):
    firebase_id: str
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
    user_name: str
    user_contact: int
    address_id: int
    # track_id: int
    order_status: str
    image_status: str
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


class TrackingStageSchema(BaseModel):
    ordered: datetime
    under_process: datetime
    shipped: datetime
    delivered: datetime

    class Config:
        from_attributes = True


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


class FavItem(BaseModel):
    product_id: int
    variant_id: int
    shop_id: int
    user_id: int

    class Config:
        from_attributes = True


class Review(BaseModel):
    rating: int
    review_text: str

    class Config:
        from_attributes = True


class Companies(BaseModel):
    company_id: Optional[int] | None = None
    company_name: str
    company_password: str | None = None
    company_domain: str
    company_logo: str
    company_email: EmailStr | None = None
    services: str
    company_contact: int
    company_address: str
    white_labelled: bool = True

    class Config:
        from_attributes = True


class CompanyUpdateDetails(BaseModel):
    company_name: str
    company_domain: str
    company_contact: int
    company_address: str
    white_labelled: bool = True

    class Config:
        from_attributes = True




class CompanySignUp(BaseModel):
    company_id: Optional[str] | None = None
    company_email: str | None = None
    company_contact: int | None = None
    company_password: str

    class Config:
        from_attributes = True


class LoginFlow(BaseModel):
    company_contact: int | None = None
    company_email: str | None = None
    employee_contact: int | None = None
    login_password: str
class Config:
    from_attributes = True


class Branch(BaseModel):
    branch_name: str
    branch_address: str
    branch_email: str
    branch_number: int
    company_id: str | None = None

    class Config:
        from_attributes = True


class Employee(BaseModel):
    employee_id: int | None = None
    employee_name: str | None = None
    employee_contact: int | None = None
    employee_password: str | None = None
    employee_gender: str | None = None
    branch_id: int | None = None


class Role(BaseModel):
    role_id: int | None = None
    role_name: str
    dashboard_feature: bool | None = None
    orders_feature: bool | None = None
    products_feature: bool | None = None
    insights_feature: bool | None = None
    employee_id: int | None = None

class NewUsers(BaseModel):
    user_uniqueid: int | None = None
    user_name: str | None = None
    user_contact: str | None = None
    user_birthdate: str | None = None
    user_image: str | None = None
    user_emailId: str | None = None
    user_password: str

class ProductInput(BaseModel):
    product_name: str
    brand_name: str
    description: str
    category_name: str
    variant_cost: float
    discounted_cost: float
    stock: int
    quantity: int
    measuring_unit: str


class ProductUpdateInput(BaseModel):
    variant_cost: float
    quantity: int
    discounted_cost: float
    stock: int
    measuring_unit: str


class EditCategoryName(BaseModel):
    category_name: str


class OrderSchema(BaseModel):
    order_id: int
    order_no: str
    customer_contact: int
    product_list: List[dict]
    total_order: float
    gst_charges: float
    additional_charges: float
    company_name: str
    company: dict
    customer: dict

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    order_no: str
    customer_contact: Optional[int]
    product_list: List[dict]
    total_order: float
    gst_charges: float
    additional_charges: float
    to_pay: float
    payment_type: str


class ImageDeleteRequest(BaseModel):
    image_url: str


class ProductItem(BaseModel):
    product_id: int
    image: str
    variant_cost: float
    quantity: int
    product_name: str
    stock: int


class ProductDetailResponse(BaseModel):
    product_name: str
    brand_name: str
    description: str
    category_name: str
    image: list
    variant_cost: float
    discounted_cost: float
    quantity: int
    stock: int
    measuring_unit: str



