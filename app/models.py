from sqlalchemy import Column, String, BIGINT, Date, JSON, ForeignKey, Time, Boolean, Float, Integer, DateTime
from sqlalchemy.orm import validates, relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base
from sqlalchemy.orm import composite


class Companies(Base):
    __tablename__ = "companies"

    company_id = Column(BIGINT, nullable=False, autoincrement=True, unique=True)
    company_name = Column(String, nullable=False, primary_key=True, unique=True)
    password = Column(String, primary_key=True, nullable=False)
    email = Column(String, nullable=False)
    company_contact = Column(BIGINT, nullable=True)
    company_address = Column(String, nullable=False)
    white_labelled = Column(Boolean, nullable=False)

    @validates('company_name', 'password', 'email', 'company_contact', 'company_address')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class Categories(Base):
    __tablename__ = "categories"

    category_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True, unique=True)
    category_name = Column(String, nullable=False)
    category_image = Column(String, nullable=False)

    @validates('category_name', 'category_image')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value

class Shops(Base):
    __tablename__ = "shops"
    shop_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True)
    shop_name = Column(String, nullable=False)
    shop_description = Column(String, nullable=True)
    shop_image = Column(String, nullable=True)
    shop_contact = Column(BIGINT, nullable=False)
    is_available = Column(Boolean, nullable=False)
    product_id = Column(BIGINT, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(BIGINT, ForeignKey("product_variants.variant_id", ondelete="CASCADE"), nullable=True)

    product = relationship("Products")
    variants = relationship("ProductVariant")


class Products(Base):
    __tablename__ = "products"

    product_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True, unique=True, index=True)
    company_name = Column(String, ForeignKey(
        "companies.company_name", ondelete="CASCADE"), nullable=False)
    category_id = Column(BIGINT, ForeignKey(
        "categories.category_id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(BIGINT, ForeignKey(
        "brands.brand_id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String, nullable=False)
    image = Column(JSON, nullable=False)
    deal = Column(Boolean, nullable=False)
    item_count = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    discount = Column(Integer, nullable=False)
    discounted_cost = Column(Float, nullable=True)
    details = Column(String, nullable=False)
    description = Column(String, nullable=True)
    weight = Column(String, nullable=False)

    company = relationship("Companies")
    brand = relationship("Brand")
    category = relationship("Categories")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    variant_id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    variant_price = Column(Float, nullable=False)
    variant_name = Column(String, nullable=False)
    brand_name = Column(String, nullable=False)
    image = Column(JSON, nullable=False)
    discounted_cost = Column(Float, nullable=True)
    discount = Column(String, nullable=True)
    item_count = Column(Integer, nullable=False)
    weight = Column(String, nullable=False)
    product_id = Column(BIGINT, ForeignKey(
        "products.product_id", ondelete="CASCADE"), nullable=False)


class Image(Base):
    __tablename__ = "images"
    id = Column(BIGINT, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)


class User(Base):
    __tablename__ = "customers"

    customer_id = Column(String, nullable=False, unique=True)
    customer_name = Column(String, nullable=False)
    customer_contact = Column(BIGINT, primary_key=True, nullable=False)
    customer_birthdate = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    email_id = Column(String, nullable=True)
    wallet = Column(Float, nullable=False)
    prev_pay_mode = Column(String, nullable=False)

    @validates('customer_name', 'customer_contact', 'customer_id')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class CompositeKey:
    def __init__(self, company_name, user_contact):
        self.company_name = company_name
        self.user_contact = user_contact

    def __composite_values__(self):
        return self.company_name, self.user_contact


class UserCompany(Base):
    __tablename__ = "user_companies"

    company_name = Column(String, ForeignKey(
        "companies.company_name", ondelete="CASCADE"), nullable=False, primary_key=True)
    user_contact = Column(BIGINT, ForeignKey(
        "customers.customer_contact", ondelete="CASCADE"), nullable=False, primary_key=True)
    composite_key = composite(CompositeKey, company_name, user_contact)

    customer = relationship("User")
    company = relationship("Companies")

    @validates('company_name', 'user_contact')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class Addresses(Base):
    __tablename__ = "address"

    address_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True)
    user_contact = Column(BIGINT, ForeignKey(
        "customers.customer_contact", ondelete="CASCADE"), nullable=False)
    address_type = Column(String, nullable=False)
    address_name = Column(String, nullable=False)
    phone_no = Column(BIGINT, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(BIGINT, nullable=False)

    customer = relationship("User")

    @validates('address_name', 'city', 'pincode', 'state', 'phone_no')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class Cart(Base):
    __tablename__ = "carts"
    cart_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(BIGINT, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    customer_contact = Column(BIGINT, ForeignKey("customers.customer_contact", ondelete="CASCADE"), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.coupon_id", ondelete="CASCADE"), nullable=True)
    products = Column(JSON, nullable=True)
    # creation_time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    company = relationship("Companies")
    user = relationship("User")
    coupon = relationship("Coupon")

    @validates( 'company_id', 'customer_contact')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class PromotionalBanners(Base):
    __tablename__ = "banners"
    banner_id = Column(Integer, primary_key=True, index=True)
    banner_image = Column(JSON, nullable=False)
    description = Column(String, nullable=True)
    discount = Column(String, nullable=False)
    isActive = Column(Boolean, nullable=False)
    tAc = Column(String, nullable=False)


class Bookings(Base):
    __tablename__ = "bookings"

    order_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey(
        "carts.cart_id", ondelete="CASCADE"), nullable=True)
    user_contact = Column(BIGINT, ForeignKey(
        "customers.customer_contact", ondelete="CASCADE"), nullable=False)
    address_id = Column(BIGINT, ForeignKey(
        "address.address_id", ondelete="CASCADE"), nullable=False)
    item_count = Column(BIGINT, nullable=False)
    order_placed = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    order_confirmation = Column(DateTime, nullable=True)
    order_shipped = Column(DateTime, nullable=True)
    total_price = Column(String, nullable=False)
    payment_type = Column(String, nullable=False)
    products = Column(JSON, nullable=False)

    customer = relationship("User")
    address = relationship('Addresses')
    cart = relationship("Cart")

    # company = relationship("Companies")

    @validates('user_contact', 'address_id')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class Coupon(Base):
    __tablename__ = "coupons"

    coupon_id = Column(Integer, autoincrement=True, primary_key=True)
    coupon_name = Column(String, nullable=True)
    coupon_image = Column(String, nullable=False)
    discount_amount = Column(Float, nullable=False)
    isActive = Column(Boolean, nullable=False)
    description = Column(String, nullable=False)


class Brand(Base):
    __tablename__ = "brands"

    brand_id = Column(BIGINT, autoincrement=True, primary_key=True)
    brand_name = Column(String, nullable=False)
    brand_image = Column(String, nullable=False)
