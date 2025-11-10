from sqlalchemy import create_engine
from sqlalchemy.orm import Query, declarative_base, scoped_session, sessionmaker

from app.core.environs import DATABASE_URL


class SoftDeleteQuery(Query):
    def not_deleted(self):
        return self.filter_by(is_deleted=False)

    def get(self, ident):
        obj = super().get(ident)
        if obj and hasattr(obj, "is_deleted") and getattr(obj, "is_deleted") == True:
            return None
        return obj

    def first_not_deleted(self):
        return self.not_deleted().first()


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, query_cls=SoftDeleteQuery)
Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)
    print("База Данных успешно инициализирована")


def drop_all():
    Base.metadata.drop_all(bind=engine)
