from sqlalchemy import Column, String, BIGINT, Date, JSON, ForeignKey, CheckConstraint, Time, Boolean, Float, Integer, \
    DateTime
from sqlalchemy.orm import validates, relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base
from sqlalchemy.orm import composite


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True, unique=True)
    category_name = Column(String, nullable=False)

    @validates('category_name')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        return value


class Products(Base):
    __tablename__ = "products"

    product_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True, unique=True, index=True)
    brand_id = Column(BIGINT, ForeignKey("brands.brand_id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String, nullable=False)
    category_id = Column(BIGINT, ForeignKey("categories.category_id", ondelete="CASCADE"), nullable=False)


    category = relationship("Category")
    brand = relationship("Brand")


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
    barcode_no = Column(BIGINT, nullable=True, unique=True)
    product_id = Column(BIGINT, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(BIGINT, ForeignKey("branch.branch_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BIGINT, ForeignKey("new_users.user_uniqueid", ondelete="CASCADE"), nullable=False)

    product = relationship("Products")
    branch = relationship("Branch")
    user = relationship("NewUsers")

# class Shops(Base):
#     __tablename__ = "shops"
#
#     shop_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True)
#     shop_name = Column(String, nullable=False)
#     shop_description = Column(String, nullable=True)
#     shop_image = Column(String, nullable=True)
#     shop_contact = Column(BIGINT, nullable=False)
#     shop_address = Column(String, nullable=True)
#     shop_coordinates = Column(String, nullable=True)
#     shop_mok = Column(String, nullable=True)
#     shop_service = Column(String, nullable=True)
#     is_available = Column(Boolean, nullable=False)
#     company_name = Column(String, ForeignKey(
#         "companies.company_name", ondelete="CASCADE"), nullable=False)
#
#     company = relationship("Companies")


class Image(Base):
    __tablename__ = "images"

    id = Column(BIGINT, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)


# class User(Base):
#     __tablename__ = "customers"
#
#     firebase_id = Column(String, nullable=False, unique=True)
#     customer_name = Column(String, nullable=False)
#     customer_contact = Column(BIGINT, primary_key=True, nullable=False)
#     customer_birthdate = Column(Date, nullable=True)
#     created_at = Column(TIMESTAMP(timezone=True),
#                         nullable=False, server_default=text('now()'))
#     profile_image = Column(String, nullable=False)
#     email_id = Column(String, nullable=True)
#     wallet = Column(Float, nullable=False)
#     prev_pay_mode = Column(String, nullable=False)
#
#     @validates('customer_name', 'customer_contact', 'customer_id')
#     def empty_string_to_null(self, key, value):
#         if isinstance(value, str) and value == '':
#             return None
#         else:
#             return value
#
#
# class CompositeKey:
#     def __init__(self, company_name, user_contact):
#         self.company_name = company_name
#         self.user_contact = user_contact
#
#     def __composite_values__(self):
#         return self.company_name, self.user_contact
#
#
# class UserCompany(Base):
#     __tablename__ = "user_companies"
#
#     company_name = Column(String, ForeignKey(
#         "companies.company_name", ondelete="CASCADE"), nullable=False, primary_key=True)
#     user_contact = Column(BIGINT, ForeignKey(
#         "customers.customer_contact", ondelete="CASCADE"), nullable=False, primary_key=True)
#     composite_key = composite(CompositeKey, company_name, user_contact)
#
#     customer = relationship("User")
#     company = relationship("Companies")
#
#     @validates('company_name', 'user_contact')
#     def empty_string_to_null(self, key, value):
#         if isinstance(value, str) and value == '':
#             return None
#         else:
#             return value
#
#
# class Addresses(Base):
#     __tablename__ = "address"
#
#     address_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True)
#     user_contact = Column(BIGINT, ForeignKey(
#         "customers.customer_contact", ondelete="CASCADE"), nullable=False)
#     address_type = Column(String, nullable=False)
#     address_name = Column(String, nullable=False)
#     phone_no = Column(BIGINT, nullable=False)
#     city = Column(String, nullable=False)
#     state = Column(String, nullable=False)
#     pincode = Column(BIGINT, nullable=False)
#     name = Column(String, nullable=True)
#
#     customer = relationship("User")
#
#     @validates('address_name', 'city', 'pincode', 'state', 'phone_no')
#     def empty_string_to_null(self, key, value):
#         if isinstance(value, str) and value == '':
#             return None
#         else:
#             return value


# class CartItem(Base):
#     __tablename__ = "cart_items"
#     cartItem_id = Column(Integer, primary_key=True, autoincrement=True)
#     cart_id = Column(Integer, ForeignKey(
#         "carts.cart_id", ondelete="CASCADE"), nullable=False)
#     product_id = Column(BIGINT, ForeignKey(
#         "products.product_id", ondelete="CASCADE"), nullable=False)
#     variant_id = Column(BIGINT, ForeignKey(
#         "product_variants.variant_id", ondelete="CASCADE"), nullable=False)
#     count = Column(BIGINT, nullable=True)
#
#     product = relationship("Products")
#     variant = relationship("ProductVariant")
#     cart = relationship('Cart')
#
#
# class Cart(Base):
#     __tablename__ = "carts"
#     cart_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     company_id = Column(BIGINT, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
#     customer_contact = Column(BIGINT, ForeignKey("customers.customer_contact", ondelete="CASCADE"), nullable=False)
#     # coupon_id = Column(Integer, ForeignKey("coupons.coupon_id", ondelete="CASCADE"), nullable=True)
#     products = Column(JSON, nullable=True)
#     # creation_time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
#
#     company = relationship("Companies")
#     user = relationship("User")
#     cart_items = relationship('CartItem', back_populates='cart')
#
#     # coupon = relationship("Coupon")
#
#     @validates('company_id', 'customer_contact')
#     def empty_string_to_null(self, key, value):
#         if isinstance(value, str) and value == '':
#             return None
#         else:
#             return value
#
#
# class PromotionalBanners(Base):
#     __tablename__ = "banners"
#     banner_id = Column(Integer, primary_key=True, index=True)
#     banner_image = Column(JSON, nullable=False)
#     description = Column(String, nullable=True)
#     discount = Column(String, nullable=False)
#     isActive = Column(Boolean, nullable=False)
#     tAc = Column(String, nullable=False)
#
#
# class Bookings(Base):
#     __tablename__ = "bookings"
#
#     order_id = Column(BIGINT, nullable=False, primary_key=True, autoincrement=True)
#     cart_id = Column(Integer, ForeignKey(
#         "carts.cart_id", ondelete="CASCADE"), nullable=True)
#     user_contact = Column(BIGINT, ForeignKey(
#         "customers.customer_contact", ondelete="CASCADE"), nullable=True)
#     address_id = Column(BIGINT, ForeignKey(
#         "address.address_id", ondelete="CASCADE"), nullable=True)
#     # track_id = Column(BIGINT, ForeignKey(
#     #     "tracking_stages.track_id", ondelete="CASCADE"), nullable=True)
#     user_name = Column(String, nullable=False)
#     order_status = Column(String, nullable=True)
#     image_status = Column(String, nullable=True)
#     order_number = Column(String, nullable=False, unique=True)
#     order_date = Column(Date, nullable=False)
#     product_total = Column(Float, nullable=False)
#     order_amount = Column(Float, nullable=False)
#     delivery_fees = Column(Float, nullable=False)
#     invoice_number = Column(String, nullable=False, unique=True)
#     invoice_amount = Column(Float, nullable=False)
#     products = Column(JSON, nullable=False)
#
#     customer = relationship("User")
#     address = relationship('Addresses')
#     cart = relationship("Cart")
#     # track = relationship("TrackingStage")
#
#
# class TrackingStage(Base):
#     __tablename__ = "tracking_stages"
#
#     track_id = Column(Integer, primary_key=True, index=True)
#     booking_id = Column(Integer, ForeignKey("bookings.order_id", ondelete="CASCADE"), nullable=True)
#     ordered = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
#     under_process = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
#     shipped = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
#     delivered = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
#
#     booking = relationship("Bookings")
#
#     @validates('track_id')
#     def empty_string_to_null(self, key, value):
#         if isinstance(value, str) and value == '':
#             return None
#         else:
#             return value
#
#
# class Coupon(Base):
#     __tablename__ = "coupons"
#
#     coupon_id = Column(Integer, autoincrement=True, primary_key=True)
#     coupon_name = Column(String, nullable=True)
#     coupon_image = Column(String, nullable=False)
#     discount_amount = Column(Float, nullable=False)
#     isActive = Column(Boolean, nullable=False)
#     description = Column(String, nullable=False)


class Brand(Base):
    __tablename__ = "brands"

    brand_id = Column(BIGINT, autoincrement=True, primary_key=True)
    brand_name = Column(String, nullable=False)
    brand_image = Column(String, nullable=False)


# class ProductCompositeKey:
#     def __init__(self, product_id, category_id):
#         self.product_id = product_id
#         self.category_id = category_id
#
#     def __composite_values__(self):
#         return self.product_id, self.category_id


# class CategoryProduct(Base):
#     __tablename__ = "product_categories"
#
#     product_id = Column(BIGINT, ForeignKey(
#         "products.product_id", ondelete="CASCADE"), nullable=False, primary_key=True)
#     category_id = Column(BIGINT, ForeignKey(
#         "categories.category_id", ondelete="CASCADE"), nullable=False, primary_key=True)
#     composite_key = composite(ProductCompositeKey, product_id, category_id)
#
#     customer = relationship("Products")
#     company = relationship("Categories")
#
#     @validates('company_name', 'user_contact')
#     def empty_string_to_null(self, key, value):
#         if isinstance(value, str) and value == '':
#             return None
#         else:
#             return value


# class Deals(Base):
#     __tablename__ = "deals"
#
#     deal_id = Column(Integer, primary_key=True, autoincrement=True)
#     shop_id = Column(Integer, ForeignKey(
#         "shops.shop_id", ondelete="CASCADE"), nullable=False)
#     product_id = Column(BIGINT, ForeignKey(
#         "products.product_id", ondelete="CASCADE"), nullable=False)
#     deal_name = Column(String, nullable=False)
#     deal_type = Column(String, nullable=False)
#     deal_description = Column(String, nullable=False)
#     deal_discount = Column(Integer, nullable=False)
#     deal_start = Column(DateTime, nullable=False)
#     deal_end = Column(DateTime, nullable=False)
#
#     product = relationship("Products")
#     shop = relationship("Shops")


# class ShopAssociation(Base):
#     __tablename__ = "shop_variants"
#
#     shop_ass_id = Column(Integer, nullable=False, primary_key=True)
#     product_id = Column(BIGINT, ForeignKey(
#         "products.product_id", ondelete="CASCADE"))
#     variant_id = Column(BIGINT, ForeignKey(
#         "product_variants.variant_id", ondelete="CASCADE"), nullable=True)
#     shop_id = Column(BIGINT, ForeignKey(
#         "shops.shop_id", ondelete="CASCADE"), nullable=True)
#
#     variant = relationship("ProductVariant")
#     product = relationship("Products")
#     shop = relationship("Shops")
#
# class FreatureList(Base):
#     __tablename__ = "feature"
#
#     feature_id = Column(Integer, primary_key=True, autoincrement=True)
#     shop_id = Column(Integer, ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
#     feature_image = Column(JSON, nullable=False)
#
#     shop = relationship("Shops")
#
#
# class FavItem(Base):
#     __tablename__ = "favitems"
#
#     fav_item_id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
#     user_id = Column(BIGINT, ForeignKey("customers.customer_contact", ondelete="CASCADE"), nullable=True)
#     variant_id = Column(Integer, ForeignKey("product_variants.variant_id", ondelete="CASCADE"), nullable=True)
#     product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=True)
#     shop_id = Column(Integer, ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=True)
#     variant = relationship("ProductVariant")
#     product = relationship("Products")
#
#     shop = relationship("Shops")
#     customer = relationship("User")
#
#     @validates('user_id')
#     def empty_string_to_null(self, key, value):
#         if isinstance(value, str) and value == '':
#             return None
#         else:
#             return value
#
#
# class Review(Base):
#     __tablename__ = "reviews"
#
#     review_id = Column(BIGINT, primary_key=True, autoincrement=True)
#     product_id = Column(BIGINT, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=True)
#     user_id = Column(BIGINT, ForeignKey("customers.customer_contact", ondelete="CASCADE"), nullable=True)
#     rating = Column(Integer, nullable=False)
#     review_text = Column(String, nullable=False)
#     review_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
#
#     product = relationship("Products")
#     customer = relationship("User")


class Companies(Base):
    __tablename__ = "companies"

    company_id = Column(String, nullable=True, primary_key=True, unique=True)
    # company_name = Column(String, nullable=False, primary_key=True, unique=True)
    company_name = Column(String, nullable=True, unique=True)
    company_password = Column(String, nullable=False)
    company_domain = Column(String, nullable=True)
    company_logo = Column(JSON, nullable=True)
    company_email = Column(String, nullable=True)
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
    branch_name = Column(String, nullable=False)
    branch_address = Column(String, nullable=False)
    branch_email = Column(String, nullable=False)
    branch_number = Column(BIGINT, nullable=False)
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


#
# class Order(Base):
#     __tablename__ = "orders"
#
#     order_id = Column(Integer, primary_key=True, autoincrement=True)
#     order_no = Column(String, nullable=False, unique=True)
#     product_list = Column(JSON, nullable=False)
#     total_order = Column(Float, nullable=True)
#     gst_charges = Column(Float, nullable=False, server_default=text('25'))
#     additional_charges = Column(Float, nullable=False, server_default=text('25'))
#     to_pay = Column(Float, nullable=False)
#     customer_contact = Column(BIGINT, ForeignKey("customer.customer_contact", ondelete="CASCADE"), nullable=True)
#
#     customer = relationship("Customer")
#
#
# class Payment(Base):
#     __tablename__ = "payments"
#
#     payment_id = Column(Integer, primary_key=True, autoincrement=True)
#     order_id = Column(Integer, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
#     payment_type = Column(String, nullable=False)
#
#     __table_args__ = (
#         CheckConstraint(
#             payment_type.in_(["Bankcard", "UPI", "Cash", "Other"]),
#             name="payment_type"
#         ),
#     )
#
#     order = relationship("Order")


class Customer(Base):
    __tablename__ = "customer"

    customer_contact = Column(BIGINT, primary_key=True, nullable=True, unique=True)
    customer_uniqueid = Column(BIGINT, primary_key=True, nullable=False,
                               server_default=text("EXTRACT(EPOCH FROM NOW())::BIGINT"))
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)


class NewUsers(Base):
    __tablename__ = "new_users"

    user_uniqueid = Column(BIGINT, primary_key=True, nullable=False,
                           server_default=text("EXTRACT(EPOCH FROM NOW())::BIGINT"))
    user_name = Column(String, nullable=True)
    user_contact = Column(BIGINT, nullable=True)
    user_birthdate = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    user_image = Column(String, nullable=True)
    user_emailId = Column(String, nullable=True)
    user_password = Column(String, nullable=True)

    @validates('user_contact', 'user_uniqueid')
    def empty_string_to_null(self, key, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value


class Stock(Base):
    __tablename__ = "stock"

    stock_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    stock_order_count = Column(Integer, nullable=False)
    seller = Column(Integer, nullable=True)
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.variant_id", ondelete="CASCADE"), nullable=False)
    date_of_shipment = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    expiry_date = Column(String, nullable=False)

    product = relationship("Products")
    variant = relationship("ProductVariant")
