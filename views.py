import random
import string
from flask_bootstrap import Bootstrap
from uploader import save_file
from forms import LoginForm, RegisterForm
from flask_login import LoginManager, login_user, login_required, logout_user
from flask import Flask,\
    jsonify,\
    request,\
    render_template,\
    flash,\
    session as login_session,\
    url_for,\
    make_response,\
    redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Category, ItemCategory
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json
import httplib2
import requests
app = Flask(__name__)
Bootstrap(app)

engine = create_engine('sqlite:///ItemCatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu App"

login_Manager = LoginManager()
login_Manager.init_app(app)
login_Manager.login_view = 'login'


@app.route('/')
@app.route('/categories/')
def view_categories():
        categories = session.query(Category).all()
        recent_items = session.query(ItemCategory).order_by(ItemCategory.created.desc()).all()
        return render_template('index.html', categories=categories, latest=recent_items)


@app.route('/categories/new/', methods={"POST", "GET"})
@login_required
def create_category():
    button_value = 'Add'
    if request.method == "POST":
        name = request.form['name']
        # Add New Category
        if name:
            category = Category(name=name)
            session.add(category)
            session.commit()
            flash("Category %s Added " % category.name)
            return redirect(url_for('view_categories'))
        # the Field of name is empty
        else:
            flash("Enter The Name Of Category")
            return render_template("newCategory.html", button_value=button_value)
    elif request.method == "GET":
        return render_template("newCategory.html", button_value=button_value)


@app.route('/categories/<int:category_id>/')
def view_category(category_id):
    category = session.query(Category).filter_by(id=category_id).one_or_none()
    items = session.query(ItemCategory).filter_by(category_id=category_id).all()
    return render_template('category.html', category=category, items=items)


@app.route('/categories/<int:category_id>/update/', methods={"POST", "GET"})
@login_required
def update_category(category_id):
    category = session.query(Category).filter_by(id=category_id).one_or_none()
    button_value = 'update'
    text = ''
    if category:
        text = category.name
    if request.method == "GET":
        return render_template('newCategory.html', text=text, button_value=button_value, category_id=category_id)
    elif request.method == "POST":
        name = request.form['name']
        if name:
            # check if The User change name oR not
            if name == category.name:
                flash("no updated Done Please Change The name")
                return render_template('newCategory.html',
                                       text=text, button_value=button_value, category_id=category_id)
            else:
                category.name = name
                session.commit()
                flash("%s Category Changed To %s" % (category.name, name))
                return redirect(url_for("view_categories"))
        # Field name was Empty
        else:
            flash("Plese Enter The Name Of Category")
            return render_template('newCategory.html', text=text, button_value=button_value, category_id=category_id)


# Item CRUD
@app.route('/categories/<int:category_id>/items/<int:item_id>')
def view_item(category_id, item_id):
        item = session.query(ItemCategory).filter_by(id=item_id, category_id=category_id).one_or_none()
        return render_template('itemcatlog.html', item=item)


@app.route('/categories/<int:category_id>/items/new/', methods={"GET", "POST"})
@login_required
def create_item(category_id):
    category = session.query(Category).filter_by(id=category_id).one_or_none()
    if request.method == "GET":
        return render_template('newItem.html', category=category)
    elif request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        # check if user enter all fields or not
        if not name or not description:
            flash("Please Enter All Fields")
            return render_template('newItem.html', category=category)
        # all things ok save item
        else:
            item_category = ItemCategory(name=name, description=description, category_id=category_id, user_id=1)
            session.add(item_category)
            session.commit()
            flash('%s item Added Successfully' % item_category.name)
            return redirect(url_for('view_category', category_id=category_id))


@app.route('/categories/<int:category_id>/items/<int:item_id>/update/', methods={"GET", "POST"})
@login_required
def update_item(category_id, item_id):
    item = session.query(ItemCategory).filter_by(id=item_id, category_id=category_id).one_or_none()
    if request.method == "GET":
        return render_template('updateItem.html', category_id=category_id, item=item)
    elif request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        if name and description:
            item.name = name
            item.description = description
            session.commit()
            flash("Item Updated Successfully")
            return redirect(url_for('view_item', category_id=category_id, item_id=item_id))
        else:
            flash('Please Enter valid Data')
            return render_template('updateItem.html', category_id=category_id, item=item)


@app.route('/categories/<int:category_id>/items/<int:item_id>/delete/', methods={"GET", "POST"})
@login_required
def delete_item(category_id, item_id):
    item = session.query(ItemCategory).filter_by(category_id=category_id, id=item_id).one_or_none()
    if request.method == "GET":
        return render_template('deleteItem.html', item=item)
    elif request.method == "POST":
        flash("%s Item Deleted Successful" % item.name)
        session.delete(item)
        session.commit()
        return redirect(url_for('view_category', category_id=category_id))


# JSON endpoint
@app.route('/categories.json')
def get_categories():
    categories = session.query(Category).all()
    js = {}
    content = []
    for category in categories:
        s = {
            'name': category.name,
            'id':  category.id
        }
        items_category = session.query(ItemCategory).filter_by(category_id=category.id).all()
        s['Item'] = [i.sirlize for i in items_category]
        content.append(s)
    js['categories'] = content
    return jsonify(js)


# login and authentication Function
@login_Manager.user_loader
def load_user(user_id):
    return session.query(User).filter_by(id=int(user_id)).one_or_none()


@app.route('/login/', methods={"GET", "POST"})
def login():
    form = LoginForm(request.form)
    page_name = 'Login'
    if request.method == "POST":
        if form.validate_on_submit():
            user = session.query(User).filter_by(email=form.email.data).one_or_none()
            if not user or user.password_hash is None or not user.verify_pasword(form.password.data):
                flash('Error Unknown Username Or Password ')
                return redirect(request.url)
            else:
                login_session['id'] = user.id
                login_session['username'] = user.name
                login_session['email'] = user.email
                login_session['picture'] = user.picture
                login_session['provider'] = 'website'
                login_user(user, remember=form.remember.data)
                return redirect(url_for('view_categories'))
    state = ''.join(random.choice(string.uppercase + string.digits)for i in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, form=form, page_name=page_name, login=True)


@app.route('/signup/', methods={"GET", "POST"})
def singup():
    form = RegisterForm(request.form)
    page_name = 'Register'
    if request.method == "GET":
        state = ''.join(random.choice(string.uppercase + string.digits) for i in xrange(32))
        login_session['state'] = state
        return render_template('login.html', form=form, STATE=state, login=False, page_name=page_name)
    # check if the form is submitted and method is POST and check also if it validate or not
    elif form.validate_on_submit():
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return render_template('login.html', form=form, login=False, page_name=page_name)
        image = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if image.filename == '':
            flash('No selected file')
            return redirect(request.url)
        else:
            email = session.query(User).filter_by(email=form.email.data).first()
            if email:  # email user already registered
                flash('This email already used')
                return redirect(request.url)
            # all Ok saving  User
            user = User(name=form.name.data, email=form.email.data)
            user.hash_password(form.password.data)
            session.add(user)
            session.flush()
            print 'this is user ID :' + str(user.id)
            filename = save_file(request.files['file'], str(user.id))
            if filename:  # Check if the photo is saved or not
                user.picture = u'users/'+filename
                session.commit()
                return redirect(url_for('login'))
            else:  # error in saving the photo
                flash('cant save the Image')
                return redirect(request.url)
    # some error in fields it will return it
    return render_template('login.html', form=form, login=False, page_name=page_name)


# logout
@app.route('/logout')
def logout():
    if login_session['provider'] == 'google':
        disconnect()
    else:
        logout_user()

        del login_session['username']
        del login_session['id']
        del login_session['email']
    flash("You have successfully been logged out.")
    return redirect(url_for('view_categories'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'
    tempuser = session.query(User).filter_by(email=login_session['email']).one_or_none()
    # check if user already stored in Database
    if tempuser is None:
        newuser = create_user(login_session)
        login_session['id'] = newuser
    else:
        login_user(tempuser)
        login_session['id'] = tempuser.id
    flash("you are now logged in as %s" % login_session['username'])
    return "Done"


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['credentials']
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['credentials']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['gplus_id']
        del login_session['credentials']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['id']
        del login_session['provider']
        return redirect(url_for('view_categories'))


# if user enter wrong url
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', e=e), 404


def create_user(login_session_paramter):
    newuser = User(name=login_session_paramter['username'],
                   email=login_session_paramter['email'],
                   picture=login_session_paramter['picture'])
    session.add(newuser)
    session.flush()
    login_user(newuser)
    user_id = newuser.id
    session.commit()
    return user_id


if __name__ == "__main__":
    app.secret_key = "Bl7a & Not"
    app.debug = True
    app.run(host="0.0.0.0", port=5000)