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

    def read_by_fields(self, fields: list) -> Any:
        session = DBSession()
        item = session.query(self.db_class).filter(*fields).first()
        session.close()
        return item
