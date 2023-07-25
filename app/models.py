from sqlalchemy import Column, String, BIGINT, Date, Boolean
from sqlalchemy.orm import validates
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base


class User(Base):
    __tablename__ = "users"
    customer_id = Column(String, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_contact = Column(BIGINT, primary_key=True, nullable=False)
    customer_birthdate = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))

    @validates('customer_name', 'customer_contact', 'customer_id')
    def empty_string_to_null(self, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value

