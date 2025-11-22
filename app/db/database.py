from sqlalchemy import create_engine, text
from sqlalchemy.orm import Query, declarative_base, sessionmaker

from app.core.environs import DATABASE_URL


class SoftDeleteQuery(Query):
    def not_deleted(self):
        """Filter out soft-deleted records"""
        return self.filter_by(is_deleted=False)

    def get(self, ident):
        """Get record by ID, excluding soft-deleted ones."""
        obj = super().get(ident)
        if obj and hasattr(obj, "is_deleted") and getattr(obj, "is_deleted") == True:
            return None
        return obj

    def first_not_deleted(self):
        """Get first non-deleted record from query"""
        return self.not_deleted().first()


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, query_cls=SoftDeleteQuery)
Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


def drop_all():
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.commit()
