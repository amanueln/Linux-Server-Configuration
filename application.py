import hashlib
import os

import httplib2
import requests

from flask import Flask, render_template, request, \
    make_response, json, flash, redirect, jsonify, url_for
from flask import session as login_session
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from sqlalchemy import asc, desc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from modal import User, Base, Catalog, CatalogItem

# ===================
# Flask instance
# ===================
app = Flask(__name__)

# ===================
# DB
# ===================
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

# ===================
# End DB
# ===================


# ===================
# GConnect CLIENT_ID
# ===================

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


# handles login by creating a state for google sign in
@app.route("/login")
def login():
    # Create a state token to prevent request forgery.
    # Store it in the session for later validation.
    state = createStateSession()
    # Set the client ID, token state, and application name in the HTML while
    # serving it.
    return render_template('register.html',
                           CLIENT_ID=CLIENT_ID,
                           STATE=state)


# handles google sign in.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Ensure that the request is not a forgery and that the user sending
    # this connect request is the expected user.
    if request.args.get('state', '') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # checks if user is connected already and redirects.
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;border-radius: \ ' \
              '150px;-webkit-border-radius:150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# ===================
# GDisconnect CLIENT_ID
# ===================

# logs out current user
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        message = 'Current user not connected.'

        flash(message)
        return redirect(url_for('home'))

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        message = 'Successfully disconnected.'
        flash(message)
        return redirect(url_for('home'))

    else:
        message = 'Failed to revoke token for given user.'

        flash(message)
        return redirect(url_for('home'))


# ==========================
# End GDisconnect CLIENT_ID
# ==========================


# ===================
# User Helper Functions
# ===================

def createUser(login_session):
    newUser = User(username=login_session['username'],
                   email=login_session['email'],
                   user_image=login_session['picture'])

    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getStateSession():
    state = hashlib.sha256(os.urandom(1024)).hexdigest()
    stateSession = login_session['state'] = state
    return stateSession


def createStateSession():
    state = hashlib.sha256(os.urandom(1024)).hexdigest()
    stateSession = login_session['state'] = state
    return stateSession


# ===================
# End User Helper Functions
# ===================


# create new catalog
def createCatalog(name, image):
    user = session.query(User).filter_by(email=login_session['email']).first()

    new_catalog = Catalog(catalog_name=name,
                          catalog_image=image,
                          user_id=user.id)
    session.add(new_catalog)
    session.commit()


# create new Item.
def createItem(name, image, description, catId):
    user = session.query(User).filter_by(email=login_session['email']).first()
    new_item = CatalogItem(item_name=name,
                           item_image=image,
                           item_detail=description,
                           user_id=user.id,
                           catalog_id=catId
                           )

    session.add(new_item)
    session.commit()


# ===================
# Flask Routing
# ===================

# Home page
# shows latest Categories added.
@app.route('/catalog/')
@app.route("/")
def home():
    # lists current catalogs created.
    catalogMenu = session.query(Catalog).order_by(Catalog.id.desc()) \
        .limit(12).all()
    if 'username' not in login_session:
        return render_template('main.html',
                               catalog=catalogMenu,
                               CLIENT_ID=CLIENT_ID,
                               STATE=createStateSession())

    else:
        # user tracks login image: changes based on current user
        user = session.query(User) \
            .filter_by(username=login_session['username']).first()
        return render_template('main.html',
                               catalog=catalogMenu,
                               login=login_session,
                               user=user)


# one Category page that shows its list of items.
@app.route("/catalog/<int:catalog_id>/items")
def allItems(catalog_id):
    currentCatName = session.query(Catalog).filter_by(id=catalog_id) \
        .one_or_none()
    if currentCatName is None:
        newcurrentCatName = session.query(Catalog).filter_by(id=catalog_id) \
            .first
        return redirect(url_for('home', currentCatalog=newcurrentCatName))
    catalogMenu = session.query(Catalog).limit(12).all()
    currentCatalog = session.query(Catalog).filter_by(id=catalog_id).all()
    items = session.query(CatalogItem). \
        filter_by(catalog_id=catalog_id).limit(20).all()

    if 'username' not in login_session:
        return render_template('items.html',
                               catalog=catalogMenu,
                               login=login_session,
                               currentCatalog=currentCatalog,
                               CLIENT_ID=CLIENT_ID,
                               STATE=createStateSession(),
                               currentCatName=currentCatName,
                               currentItems=items)

    else:
        # user tracks login image: changes based on current user
        user = session.query(User). \
            filter_by(email=login_session['email']).first()
        return render_template('items.html',
                               catalog=catalogMenu,
                               login=login_session,
                               currentCatalog=currentCatalog,
                               user=user,
                               CLIENT_ID=CLIENT_ID,
                               STATE=createStateSession(),
                               currentCatName=currentCatName,
                               currentItems=items)


# Show Item description on page based on which item selected.
@app.route("/catalog/<int:catalog_id>/item/<int:item_id>")
def item(item_id, catalog_id):
    currentItemId = session.query(CatalogItem). \
        filter_by(id=item_id).one_or_none()
    if currentItemId is None:
        return redirect(url_for('allItems', catalog_id=catalog_id))
    catalogMenu = session.query(Catalog).limit(12).all()
    currentCatalog = session.query(Catalog).filter_by(id=catalog_id).all()
    items = session.query(CatalogItem).filter_by(id=catalog_id).limit(20).all()
    if 'username' not in login_session:
        return render_template('itemdescription.html',
                               catalog=catalogMenu,
                               login=login_session,
                               currentCatalog=currentCatalog,
                               CLIENT_ID=CLIENT_ID,
                               STATE=createStateSession(),
                               currentItemID=currentItemId,
                               currentItems=items)

    else:
        # user tracks login image: changes based on current user
        user = session.query(User).\
            filter_by(email=login_session['email']).first()
        currentItemId = session.query(CatalogItem).filter_by(id=item_id).one()
        catalogMenu = session.query(Catalog).limit(12).all()
        currentCatalog = session.query(Catalog).\
            filter_by(id=catalog_id).all()
        items = session.query(CatalogItem).\
            filter_by(id=catalog_id).limit(20).all()
        return render_template('itemdescription.html', catalog=catalogMenu,
                               user=user, login=login_session,
                               currentCatalog=currentCatalog,
                               CLIENT_ID=CLIENT_ID,
                               STATE=createStateSession(),
                               currentItemID=currentItemId,
                               currentItems=items)


# handler to create a new category
@app.route("/newcatalog", methods=['GET', 'POST'])
def newCatalog():
    if 'username' not in login_session:
        return redirect('/login')

    else:
        catalog = session.query(Catalog).\
            limit(12).all()
        user = session.query(User).\
            filter_by(email=login_session['email']).first()
        if request.method == 'POST':

            name = request.form['name'].lower()

            if name:

                image = request.form['image']
                if not image:
                    image = 'http://via.placeholder.com/360x250?text=%s IMAGE'\
                            % name.upper()
                    createCatalog(name, image)

                else:
                    createCatalog(name, image)

                return redirect(url_for('home'))
        return render_template('newcatalog.html',
                               catalog=catalog,
                               user=user,
                               login=login_session)


# handler to create a new item in a specific category
@app.route("/catalog/<int:catalog_id>/items/newitem", methods=['GET', 'POST'])
def newitem(catalog_id):
    if 'username' not in login_session:
        return redirect('/login')

    else:
        currentCatName = session.query(Catalog).\
            filter_by(id=catalog_id).one()
        items = session.query(CatalogItem).\
            filter_by(catalog_id=catalog_id).limit(20).all()
        user = session.query(User).\
            filter_by(email=login_session['email']).first()

        if request.method == 'POST':

            itemName = request.form['name'].lower()
            description = request.form['description'].lower()
            checkItem = session.query(CatalogItem).\
                filter_by(item_name=request.form['name'].lower()).first()

            if checkItem:
                message = 'item Already in system. Add another Item'
                flash(message)
                return redirect(url_for('newitem', catalog_id=catalog_id))
            else:
                image = request.form['image']
                if not image:
                    image = 'http://via.placeholder.com/360x250?text=%s IMAGE'\
                            % itemName.upper()
                    createItem(itemName,
                               image,
                               description,
                               catalog_id)
                else:
                    createItem(itemName,
                               image,
                               description,
                               catalog_id)
                return redirect(url_for('allItems', catalog_id=catalog_id))

        return render_template('newitem.html',
                               items=items,
                               user=user,
                               login=login_session,
                               currentCatName=currentCatName,
                               CLIENT_ID=CLIENT_ID)


# deletes a category
@app.route("/catalog/<int:catalog_id>/delete")
def deleteCatalog(catalog_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        # Insert a Person in the person table
        delete_catalog = session.query(Catalog).\
            filter_by(id=catalog_id).one_or_none()
        if delete_catalog is None:
            return redirect(url_for('home'))
        else:
            if login_session['username'] != delete_catalog.user.username:
                message = "you dont have permissin to delete this!!!"
                flash(message)
            else:
                delete_catalog_items = session.query(CatalogItem)\
                    .filter_by(catalog_id=catalog_id).all()
                session.delete(delete_catalog)
                for items in delete_catalog_items:
                    session.delete(items)
                    session.commit()
                session.commit()
                message = "catalog deleted!!!"
                flash(message)
            return redirect(url_for('home'))


# deletes a Item
@app.route("/catalog/<int:catalog_id>/item/<int:item_id>/delete")
def deleteItem(catalog_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        delete_item = session.query(CatalogItem).\
            filter_by(id=item_id).one_or_none()
        if delete_item is None:
            return redirect(url_for('item',
                                    catalog_id=catalog_id,
                                    item_id=item_id))
        # checks if user has permission
        if login_session['username'] != delete_item.user.username:
            message = "you dont have permissin to delete this!!!"
            flash(message)
            return redirect(url_for('allItems',
                                    catalog_id=catalog_id))

        else:
            session.delete(delete_item)
            session.commit()
            message = 'Item deleted!!!!'
            flash(message)
        return redirect(url_for('allItems',
                                catalog_id=catalog_id))


# edits item that have been created
@app.route("/catalog/<int:catalog_id>/item/<int:item_id>/edit",
           methods=['GET', 'POST'])
def editItem(catalog_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        user = session.query(User).\
            filter_by(email=login_session['email']).first()
        category = session.query(Catalog).limit(12).all()
        edit_item = session.query(CatalogItem).filter_by(id=item_id).one()
        if request.method == 'POST':
            if login_session['username'] != edit_item.user.username:
                message = 'You dont have permissin to Edit this.'

                flash(message)
                return redirect(url_for('editItem',
                                        item_id=item_id,
                                        catalog_id=catalog_id))

            else:

                edit_item.item_name = request.form['name'].lower()
                edit_item.item_image = request.form['image']
                edit_item.item_detail = request.form['description'].lower()
                edit_item.catalog_id = request.form['category'].lower()
                session.add(edit_item)
                session.commit()

                return redirect(url_for('item',
                                        item_id=item_id,
                                        catalog_id=catalog_id))

    return render_template('edititem.html',
                           edit_item=edit_item,
                           category=category,
                           user=user,
                           login=login_session)


# ===================
# End Flask Routing
# ===================

# ===================
# JSON
# ===================

@app.route('/catalog/JSON')
@app.route("/JSON")
def allcatagoriesJSON():
    categories = session.query(Catalog).all()
    category_dict = [c.serialize for c in categories]
    return jsonify(Catalog=category_dict)


@app.route('/catalog/<int:catalog_id>/items/JSON')
def categoryItemsJSON(catalog_id):
    items = session.query(CatalogItem).filter_by(catalog_id=catalog_id).all()
    return jsonify(items=[i.serialize for i in items])


# ===================
# End JSON
# ===================

if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'memcached'
    app.config['SECRET_KEY'] = 'super secret key'
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True, host='0.0.0.0', port=8080)
