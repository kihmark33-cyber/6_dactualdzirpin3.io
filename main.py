from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime, timezone, timedelta



app = Flask(__name__)
app.secret_key = "CHINA_ALWAYS_CAPYTHINA"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://flaskuser:6767@localhost/peopletalksfree'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return '<User %r>' % self.name


class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    views = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    tag = db.Column(db.String(50), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author_name = db.Column(db.String(255), nullable=False)  # додатково

    comments = db.relationship('Comment', backref='post', cascade="all, delete-orphan")



class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(250), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)



class Favorite(db.Model):
    __tablename__ = 'favorite'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete="CASCADE"), nullable=False)

#class Community(db.Model):
    #__tablename__ = 'community'
    #id = db.Column(db.Integer, primary_key=True)
    #name = db.Column(db.String(100), nullable=False, unique=True)
    #description = db.Column(db.Text, nullable=True)
    #join_mode = db.Column(db.String(20), default="public")
    ## значення: "public" або "invite_only"
    #invite_link = db.Column(db.String(200), nullable=True)
    ## зв’язок з учасниками
    #owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    #members = db.relationship('CommunityMember', backref='community', cascade="all, delete-orphan")

#class CommunityMember(db.Model):
    #__tablename__ = 'community_members'
    #id = db.Column(db.Integer, primary_key=True)
    #community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



@app.route('/')
def index():
    # Вибираємо всі пости
    posts = Post.query.all()

    # Топ-пости: сортуємо за коментарями та переглядами
    top_posts = Post.query.order_by(Post.comments_count.desc(), Post.views.desc()) \
                          .limit(5).all()

    return render_template('index.html', posts=posts, top_posts=top_posts)



@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')  # замість 'name'
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            return "Всі поля обов'язкові!"

        # логіка збереження користувача
        user = User(name=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:   # просте порівняння
            session['user_name'] = user.name     # зберігаємо ім’я у сесії
            return redirect(url_for('index'))
        else:
            return "Invalid email or password"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_name', None)
    return redirect(url_for('index'))



#@app.route('/create_community', methods=['GET', 'POST'])
#def create_community():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        join_mode = request.form['join_mode']

        user_name = session.get('user_name')
        user = User.query.filter_by(name=user_name).first()
        if not user:
            return "Ви повинні увійти, щоб створити спільноту."

        invite_link = None
        if join_mode == "invite_only":
            invite_link = f"/join/{uuid.uuid4().hex}"

        community = Community(
            name=name,
            description=description,
            join_mode=join_mode,
            invite_link=invite_link,
            owner_id=user.id   # ← ключове поле
        )
        db.session.add(community)
        db.session.commit()
        return redirect(url_for('list_communities'))

    return render_template('create_community.html')



#@app.route('/communities')
#def list_communities():
#    #communities = Community.query.all()
#    return render_template('communities.html')


@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    user_name = session.get('user_name')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tag = request.form['tag']

        if user_name:
            user = User.query.filter_by(name=user_name).first()
            if not user:
                return "Користувач не знайдений"

            post = Post(
                title=title,
                description=description,
                tag=tag,
                user_id=user.id,
                author_name=user.name
            )
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('my_posts'))
        else:
            return "Ви повинні увійти, щоб створити пост."

    return render_template('create_post.html')



@app.route('/my_posts')
def my_posts():
    user_name = session.get('user_name')
    posts = Post.query.filter_by(author_name=user_name).all()
    return render_template('my_posts.html', posts=posts)

@app.route('/delete_post/<int:id>')
def delete_post(id):
    post = db.session.get(Post, id)
    # видаляємо коментарі
    Comment.query.filter_by(post_id=post.id).delete()
    # видаляємо з обраного
    Favorite.query.filter_by(post_id=post.id).delete()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('my_posts'))



@app.route('/update_post/<int:id>', methods=['GET', 'POST'])
def update_post(id):
    post = db.session.get(Post, id)   # отримуємо пост
    if request.method == 'POST':
        post.title = request.form['title']
        post.description = request.form['description']
        post.tag = request.form['tag']
        db.session.commit()
        return redirect(url_for('my_posts'))
    return render_template('change_post.html', post=post)  # передаємо post


@app.route('/top_posts')
def top_posts():
    posts = Post.query.order_by(Post.comments_count.desc(), Post.views.desc()) \
                      .limit(10).all()
    return render_template('top_posts.html', posts=posts)

@app.route('/post/<int:id>', methods=['GET', 'POST'])
def post_detail(id):
    post = db.session.get(Post, id)

    # збільшуємо перегляди при кожному GET
    if request.method == 'GET':
        post.views += 1
        db.session.commit()

    if request.method == 'POST':
        comment_text = request.form['comment']
        new_comment = Comment(text=comment_text, post_id=post.id)
        db.session.add(new_comment)
        post.comments_count += 1
        db.session.commit()
        return redirect(url_for('post_detail', id=post.id))

    comments = Comment.query.filter_by(post_id=post.id).all()
    return render_template('post_detail.html', post=post, comments=comments)

@app.route('/payment_callback/<int:post_id>', methods=['POST'])
def payment_callback(post_id):
    data = request.json
    status = data.get("status")

    post = db.session.get(Post, post_id)
    if post and status == "success":
        post.is_paid = True
        post.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        db.session.commit()
        return "Оплата успішна"
    return "Оплата не пройшла"


@app.route('/favorite')
def favorite():
    user_name = session.get('user_name')
    user = User.query.filter_by(name=user_name).first()
    if not user:
        return redirect(url_for('login'))

    posts = Post.query.join(Favorite, Post.id == Favorite.post_id)\
                      .filter(Favorite.user_id == user.id).all()
    return render_template('favorite.html', posts=posts)


@app.route('/favorite/add/<int:post_id>', methods=['POST'])
def add_to_favorite(post_id):
    user_name = session.get('user_name')
    user = User.query.filter_by(name=user_name).first()
    if user:
        new_entry = Favorite(user_id=user.id, post_id=post_id)
        db.session.add(new_entry)
        db.session.commit()
        post = Post.query.get(post_id)
        return render_template('post_detail.html', post=post, message="Пост додано до Favorite")
    return redirect(url_for('login'))


@app.route('/favorite/remove/<int:post_id>', methods=['POST'])
def remove_from_favorite(post_id):
    user_name = session.get('user_name')
    user = User.query.filter_by(name=user_name).first()
    if user:
        entry = Favorite.query.filter_by(user_id=user.id, post_id=post_id).first()
        if entry:
            db.session.delete(entry)
            db.session.commit()
    return redirect(url_for('favorite'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    posts = []

    if query:
        posts = Post.query.filter(
            (Post.title.ilike(f"%{query}%")) |
            (Post.tag.ilike(f"%{query}%"))
        ).all()

    return render_template('search.html', posts=posts, query=query)


if __name__ == '__main__':
    app.run(debug=True)