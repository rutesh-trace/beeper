import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Integer, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase

from db_domains.db import Base


def to_dict(obj: DeclarativeBase) -> Dict[str, Any]:
    """
    Convert a SQLAlchemy model instance into a dictionary.
    """
    data = {}  # Initialize an empty dictionary

    # Iterate over all columns of the model
    for column in obj.__table__.columns.keys():
        column_name = column
        column_value = getattr(obj, column_name)
        data[column_name] = column_value

    return data


class CreateUpdateTime(Base):
    __abstract__ = True

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


@declared_attr
def created_by(cls):
    return Column(Integer, ForeignKey("users.id"), nullable=False)


@declared_attr
def modified_by(cls):
    return Column(Integer, ForeignKey("users.id"), nullable=False)
