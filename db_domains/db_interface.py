from typing import Any

from db_domains import Base, to_dict
from db_domains.db import DBSession

DataObject = dict[str, Any]


class DBInterface:
    def __init__(self, db_model: type[Base]) -> None:
        self.db_class: type[Base] = db_model

    def read_all(self) -> DataObject:
        session = DBSession()
        items = session.query(self.db_class).all()
        session.close()
        return items

    def read_by_id(self, _id: Any) -> DataObject:
        session = DBSession()
        item = session.get(self.db_class, _id)
        session.close()
        return item

    def create(self, data: DataObject) -> DataObject:
        session = DBSession()
        item: Base = self.db_class(**data)
        session.add(item)
        session.commit()
        result = to_dict(item)
        session.close()
        return result

    def update(self, _id: str, data: DataObject) -> DataObject:
        session = DBSession()
        item: Base = session.query(self.db_class).get(_id)
        for key, value in data.items():
            setattr(item, key, value)
        session.commit()
        result = to_dict(item)
        session.close()
        return result

    def read_by_fields(self, fields: list) -> Any:
        session = DBSession()
        item = session.query(self.db_class).filter(*fields).first()
        session.close()
        return item

    def read_all_by_fields(self, filters: list = None, order_by=None, order_direction: str = "asc", limit: int = None,
                           offset: int = None) -> DataObject:
        """
        Reads all records that match the provided filters.

        Args:
            filters (list): List of filter conditions.
            order_by: SQLAlchemy column to order by.
            order_direction: "asc" or "desc".
            limit (int): Number of records to fetch.
            offset (int): Number of records to skip.

        Returns:
            list[DataObject]: A list of dictionary representations of records.
        """
        session = DBSession()
        query = session.query(self.db_class)

        # Apply filters if provided
        if filters:
            query = query.filter(*filters)

        # Apply ordering if provided
        # print(f"Ordering by {order_by}")
        # if order_by:
        #     from sqlalchemy import asc, desc
        #
        #     column = getattr(self.db_class, order_by, None)
        #     if column is not None:
        #         query = query.order_by(asc(column) if order_direction == "asc" else desc(column))
        #     else:
        #         raise ValueError(f"Invalid column '{order_by}' for ordering")
        # breakpoint()

        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        items = query.all()
        session.close()

        return items  # Convert objects to dictionary format
