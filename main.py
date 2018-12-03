from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
# Note: the connection string after :// contains:
# user:password@server:portNumber/databaseName
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'h2dehp1'
db = SQLAlchemy(app)

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pub_date = db.Column(db.DateTime)
    
    def __init__(self, title, body, owner, pub_date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    username_error = ''
    password_error = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            return redirect('/newpost')
        if not user:
            return render_template('/login.html', username_error="Username doesn't exist.")
        else:
            return render_template('/login.html', password_error="Your username or password was incorrect.")

    return render_template('/login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        exist = User.query.filter_by(username=username).first()

        username_error = ''
        password_error = ''
        verify_error = ''

        if not username:
            username_error = 'Username must not be blank.'
        elif len(username) <= 3 or len(username) > 20:
            username_error = 'Username must be between 3 and 20 characters in length.'
        elif ' ' in username:
            username_error = 'Username cannot contain spaces'
        if not password:
            password_error = 'Password must not be blank.'
        elif len(password) <= 3:
            password_error = 'Password must be longer than 3 characters.'
        elif ' ' in password:
            password_error = 'Password cannot contain spaces.'
        if password != verify or verify == '':
            verify_error = 'Passwords do not match.'
        if exist:
            username_error = 'Username already in use.'

        if len(username) > 3 and len(password) > 3 and password == verify and not exist:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        else:
            return render_template('/signup.html', username=username, username_error=username_error, 
                password_error=password_error, verify_error=verify_error)

    return render_template('/signup.html')

@app.route('/blog', methods=['GET', 'POST'])
def blog():
    blog_id = request.args.get('id')
    user_id = request.args.get('userid')
    posts = Blog.query.order_by(Blog.pub_date.desc())

    if blog_id:
        post = Blog.query.filter_by(id=blog_id).first()
        return render_template('post.html', title=post.title, body=post.body, user=post.owner.username,
            pub_date=post.pub_date, user_id=post.owner_id)
    if user_id:
        entries = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('user.html', entries=entries)

    return render_template('blog.html', posts=posts)

@app.route('/newpost')
def post():
    return render_template('newpost.html', title="New Post")

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    title = request.form['title']
    body = request.form['body']
    owner = User.query.filter_by(username=session['username']).first()

    title_error = ''
    body_error = ''

    if not title:
        title_error = 'Enter a Title.'
    if not body:
        body_error = 'Enter a something.'

    if not title_error and not body_error:
        new_post = Blog(title, body, owner)
        db.session.add(new_post)
        db.session.commit()
        page_id = new_post.id
        return redirect('/blog?id={0}'.format(page_id))
    else:
        return render_template('newpost.html', title=title, body=body, title_error=title_error,
            body_error=body_error)

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/')

if __name__ == '__main__':
    app.run()

        