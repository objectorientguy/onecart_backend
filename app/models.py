from sqlalchemy import Column, String, BIGINT, Date, JSON, ForeignKey, Time
from sqlalchemy.orm import validates, relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base


class User(Base):
    __tablename__ = "customers"
    customer_id = Column(String, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_contact = Column(BIGINT, primary_key=True, nullable=False)
    customer_birthdate = Column(Date, nullable=True)
    companies = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))

    @validates('customer_name', 'customer_contact', 'customer_id')
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
    address_title = Column(String, nullable=False)
    address_name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    pincode = Column(BIGINT, nullable=False)
    company = Column(String, nullable=False)

    customer = relationship("User")

    @validates('user_contact', 'address_title', 'address_name', 'city', 'pincode', 'company')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class UserCart(Base):
    __tablename__ = "cart"

    cart_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True)
    user_contact = Column(BIGINT, ForeignKey(
        "customers.customer_contact", ondelete="CASCADE"), nullable=False, primary_key=True)
    company_id = Column(String, nullable=False, primary_key=True)
    products = Column(JSON, nullable=False)

    customer = relationship("User")

    @validates('cart_id', 'user_contact', 'company_id')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class Bookings(Base):
    __tablename__ = "bookings"

    booking_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True)
    user_contact = Column(BIGINT, ForeignKey(
        "customers.customer_contact", ondelete="CASCADE"), nullable=False,)
    company_id = Column(String, nullable=False)
    products = Column(JSON, nullable=False )
    address_id = Column(BIGINT, ForeignKey(
        "address.address_id", ondelete="CASCADE"), nullable=False)
    booking_date = Column(Date, nullable=False)
    booking_time = Column(Time, nullable=False)
    total = Column(String, nullable=False)
    coupon = Column(String, nullable=True)
    coupon_discount = Column(String, nullable=True)

    customer = relationship("User")

    @validates('cart_id', 'user_contact', 'company_id')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value
