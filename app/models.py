from sqlalchemy import Column, String, BIGINT, Date, JSON, ForeignKey, Time, Boolean
from sqlalchemy.orm import validates, relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base
from sqlalchemy.orm import composite




class Companies(Base):
    __tablename__ = "companies"

    company_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True, unique=True)
    company_name = Column(String, nullable=False, primary_key=True, unique=True)
    password = Column(String, primary_key=True, nullable=False)
    email = Column(String, nullable=True)
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


class Products(Base):
    __tablename__ = "products"

    product_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True, unique=True)
    company_name = Column(String, ForeignKey(
        "companies.company_name", ondelete="CASCADE"), nullable=False)
    category_id = Column(BIGINT, ForeignKey(
        "categories.category_id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String, nullable=False)
    image = Column(JSON, nullable=False)
    item_count = Column(BIGINT, nullable=False)
    variants = Column(JSON, nullable=False)
    cost = Column(String, nullable=False)
    discounted_cost = Column(String, nullable=True)
    details = Column(String, nullable=False)

    company = relationship("Companies")
    category = relationship("Categories")


class Image(Base):
    __tablename__ = "images"
    id = Column(BIGINT, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)


class User(Base):
    __tablename__ = "customers"

    customer_id = Column(String, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_contact = Column(BIGINT, primary_key=True, nullable=False)
    customer_birthdate = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))

    @validates('customer_name', 'customer_contact', 'customer_id')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class CompositeKey:
    def __init__(self, company_id, user_contact):
        self.company_id = company_id
        self.user_contact = user_contact

    def __composite_values__(self):
        return self.company_id, self.company_id


class UserCompany(Base):
    __tablename__ = "user-companies"

    company_name = Column(String, ForeignKey(
        "companies.company_name", ondelete="CASCADE"), nullable=False, primary_key=True)
    user_contact = Column(BIGINT, ForeignKey(
        "customers.customer_contact", ondelete="CASCADE"), nullable=False, primary_key=True)
    composite_key = composite(CompositeKey, company_name, user_contact)

    customer = relationship("User")
    company = relationship("Companies")

    @validates('company_id', 'user_contact')
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
    phone_no = Column(BIGINT,nullable=False)
    city = Column(String, nullable=False)
    state = Column(String,nullable = False)
    pincode = Column(BIGINT, nullable=False)

    customer = relationship("User")

    @validates('user_contact', 'address_type', 'address_name', 'city', 'pincode', 'state', 'phone_no')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(BIGINT, primary_key=True, index=True, )
    product_id = Column(BIGINT, ForeignKey("products.product_id"))
    cart_id = Column(BIGINT, ForeignKey("carts.id"))

    cart = relationship("Cart", back_populates="items")


class Cart(Base):
    __tablename__ = "carts"
    id = Column(BIGINT, primary_key=True, index=True)
    company_name = Column(String, ForeignKey("companies.company_name"))
    user_id = Column(BIGINT, ForeignKey("customers.customer_contact"))

    items = relationship("CartItem", back_populates="cart")


class Bookings(Base):
    __tablename__ = "bookings"

    booking_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True)
    user_contact = Column(BIGINT, ForeignKey(
        "customers.customer_contact", ondelete="CASCADE"), nullable=False, )
    company_id = Column(String, ForeignKey(
        "companies.company_name", ondelete="CASCADE"), nullable=False)
    products = Column(JSON, nullable=False)
    address_id = Column(BIGINT, ForeignKey(
        "address.address_id", ondelete="CASCADE"), nullable=False)
    booking_date = Column(Date, nullable=False)
    booking_time = Column(Time, nullable=False)
    total = Column(String, nullable=False)
    coupon = Column(String, nullable=True)
    coupon_discount = Column(String, nullable=True)

    customer = relationship("User")
    company = relationship("Companies")

    @validates('cart_id', 'user_contact', 'company_id')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value

