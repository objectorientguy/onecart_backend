from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import date, time, datetime

class Companies(BaseModel):
    company_id: Optional[int] | None = None
    company_name: str
    company_password: str | None = None
    company_domain: str
    company_logo: str
    company_email: EmailStr | None = None
    company_description: Optional[str] = None
    services: str
    company_contact: int
    company_address: str
    white_labelled: bool = True
    class Config:
        from_attributes = True
class NewUsers(BaseModel):
    user_uniqueid: int | None = None
    user_name: str | None = None
    user_contact: str | None = None
    user_birthdate: str | None = None
    user_image: str | None = None
    user_emailId: str | None = None
    user_password: str
class EditUser(BaseModel):
    user_image: str | None = None
    user_name: str | None = None
    user_contact: str | None = None
    user_emailId: str | None = None
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
class EditEmployee(BaseModel):
    role_name: str
    employee_name: str | None = None
    employee_contact: int | None = None
    employee_gender: str | None = None
class Role(BaseModel):
    role_id: int | None = None
    role_name: str
    dashboard_feature: bool | None = None
    orders_feature: bool | None = None
    products_feature: bool | None = None
    insights_feature: bool | None = None
    employee_id: int | None = None
class ImageDeleteRequest(BaseModel):
    image_url: str
class ProductInput(BaseModel):
    category_id: int
    product_name: str
    brand_id: int
    barcode_no: int
    description: str
    variant_cost: float
    discounted_cost: float
    stock: int
    quantity: int
    measuring_unit: str


