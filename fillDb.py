from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

from  modal import *

engine = create_engine('sqlite:///item_catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Delete Categories if exisitng.
session.query(Catalog).delete()
# Delete Items if exisitng.
session.query(CatalogItem).delete()
# Delete Users if exisitng.
session.query(User).delete()

User1 = User(username="Nathan Amanuel",
             email="Nathanielamanuel@gmail.com",
             user_image='http://forums.ferra.ru/uploads/profile/photo-106401.png')
session.add(User1)
session.commit()

# Create fake categories
Category1 = Catalog(catalog_name="Sports Cars",
                    catalog_image="http://freedesignfile.com/upload/2016/02/Auto-company-logos-creative-vector-02.jpg",
                    user_id=1)
session.add(Category1)
session.commit()

# Populate a category with items for testing
# Using different users for items also
Item1 = CatalogItem(item_name="Corvette Z06",
                    date=datetime.datetime.now(),
                    item_detail='''
                                Model: 2017 Chevrolet Corvette
                                MSRP: From $79,450
                                Horsepower: 650 hp
                                Curb weight: 3,524 to 3,582 lbs
                                Engine: 6.2 L V8
                                MPG: Up to 15 city / 22 highway''',
                    item_image="http://www.larevueautomobile.com/images/Corvette/Z06/Exterieur/Corvette_Z06_005.jpg",
                    catalog_id=1,
                    user_id=1)
session.add(Item1)
session.commit()


print "Your database has been populated with fake data!"