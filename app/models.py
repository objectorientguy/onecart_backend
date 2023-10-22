from sqlalchemy import Column, String, BIGINT, Date, JSON, ForeignKey, CheckConstraint, Time, Boolean, Float, Integer, \
    DateTime
from sqlalchemy.orm import validates, relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base

class Image(Base):
    __tablename__ = "images"
    id = Column(BIGINT, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
class Brand(Base):
    __tablename__ = "brands"
    brand_id = Column(Integer, primary_key=True, index=True)
    brand_name = Column(String, unique=True, index=True)
    products = relationship("Products", back_populates="brand")
class Companies(Base):
    __tablename__ = "companies"
    company_id = Column(String, nullable=True, primary_key=True, unique=True)
    company_name = Column(String, nullable=True, unique=True)
    company_password = Column(String, nullable=False)
    company_domain = Column(String, nullable=True)
    company_logo = Column(JSON, nullable=True)
    company_email = Column(String,  nullable=True)
    company_description = Column(String, nullable=True)
    services = Column(String, nullable=True)
    company_contact = Column(BIGINT, nullable=True)
    company_address = Column(String, nullable=True)
    white_labelled = Column(Boolean, nullable=True)
    onboarding_date = Column(TIMESTAMP(timezone=True), nullable=True, server_default=text('now()'))
    @validates('company_name', 'company_password', 'company_email', 'company_contact', 'company_address')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value
class Branch(Base):
    __tablename__ = "branch"
    branch_id = Column(Integer, primary_key=True, autoincrement=True)
    branch_name = Column(String, nullable=True)
    branch_address = Column(String, nullable=True)
    branch_email = Column(String, nullable=True)
    branch_number = Column(BIGINT, nullable=True)
    company_id = Column(String, ForeignKey("companies.company_id", ondelete="CASCADE"))
    company = relationship("Companies")
class Employee(Base):
    __tablename__ = "employee"
    employee_id = Column(BIGINT, primary_key=True, autoincrement=True)
    employee_name = Column(String, nullable=True)
    employee_contact = Column(BIGINT, nullable=False)
    employee_password = Column(String, nullable=False)
    employee_gender = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branch.branch_id", ondelete="CASCADE"))
    branch = relationship("Branch")
class Role(Base):
    __tablename__ = "role"
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, nullable=True)
    dashboard_feature = Column(Boolean, nullable=True)
    orders_feature = Column(Boolean, nullable=True)
    products_feature = Column(Boolean, nullable=True)
    insights_feature = Column(Boolean, nullable=True)
    employee_id = Column(Integer, ForeignKey("employee.employee_id", ondelete="CASCADE"))
    employee = relationship("Employee")
class NewUsers(Base):
    __tablename__ = "new_users"
    user_uniqueid = Column(BIGINT, primary_key=True, nullable=False, server_default=text("EXTRACT(EPOCH FROM NOW())::BIGINT"))
    user_name = Column(String, nullable=True)
    user_contact = Column(BIGINT, nullable=True)
    user_birthdate = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    user_image = Column(String, nullable=True)
    user_emailId = Column(String, nullable=True)
    user_password = Column(String, nullable=True)
    # company_id = Column(String, ForeignKey("companies.company_id", ondelete="CASCADE"))
    # branch_id = Column(BIGINT, ForeignKey("branch.branch_id", ondelete="CASCADE"))
    #
    # company = relationship("Companies")
    # branch = relationship("Branch")

class Categories(Base):
    __tablename__ = "categories"
    category_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True, unique=True)
    category_name = Column(String, nullable=True)
    category_image = Column(String, nullable=True)
    @validates('category_name', 'category_image')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value
class Products(Base):
    __tablename__ = "products"
    product_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True, unique=True, index=True)
    product_name = Column(String, nullable=False)
    category_id = Column(BIGINT, ForeignKey("categories.category_id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(BIGINT, ForeignKey("brands.brand_id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(BIGINT, ForeignKey("branch.branch_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BIGINT, ForeignKey("new_users.user_uniqueid", ondelete="CASCADE"), nullable=False)

    brand = relationship("Brand")
    category = relationship("Categories")
    branch = relationship("Branch")
    user = relationship("NewUsers")
class ProductVariant(Base):
    __tablename__ = "product_variants"
    variant_id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    variant_cost = Column(Float, nullable=False)
    brand_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    discounted_cost = Column(Float, nullable=True)
    discount = Column(BIGINT, nullable=True)
    stock = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    image = Column(JSON, nullable=True)
    ratings = Column(Integer, nullable=True)
    measuring_unit = Column(String, nullable=False)
    barcode_no = Column(BIGINT, nullable=False, unique=True)
    product_id = Column(BIGINT, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    product = relationship("Products")
