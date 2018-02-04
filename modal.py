import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String,DateTime
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# User database
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    password = Column(String(250))
    user_image = Column(String(250))

#Catalog database
class Catalog(Base):
    __tablename__ = 'catalog'
    id = Column(Integer, primary_key=True)
    catalog_name = Column(String(250), nullable=False)
    catalog_image = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'catalog_name': self.catalog_name,
            'catalog_image': self.catalog_image,
        }

#Item catalog database
class CatalogItem(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    item_name = Column(String(250), nullable=False)
    date = Column(DateTime(timezone=True), default=func.now())
    item_image = Column(String(250))
    item_detail = Column(String(500))
    user_id = Column(Integer, ForeignKey('user.id'))
    catalog_id = Column(Integer, ForeignKey('catalog.id'))
    user = relationship(User)
    catalog = relationship(Catalog)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'item_name': self.item_name,
            'item_image': self.item_image,
            'item_detail': self.item_detail,
        }


# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///item_catalog.db')

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)

