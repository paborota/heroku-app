from app_data import app, User, BlogPost, Comment, db
from app_helper_functions import is_logged_in, login_failed, check_for_existing_user, get_next_page, admin_only, delete_item
from datetime import date
from flask import render_template, redirect, flash, url_for, session
from flask_login import login_user, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterNewUserForm, LoginForm, CommentForm


@app.route('/')
def get_all_posts():

    posts = db.session.query(BlogPost).all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():

    # On the off chance the user typed in the url to register:
    # Check to make sure user isn't already signed in
    if is_logged_in():
        return redirect(url_for('get_all_posts'))

    form = RegisterNewUserForm()
    if form.validate_on_submit():

        if check_for_existing_user(db=db, user_class=User, email=form.email.data):
            flash('This email is already in use.')
            session['login_email'] = form.email.data
            return redirect(url_for('login'))

        new_user = User(
            email=form.email.data,
            name=form.name.data
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()
        db.session.refresh(new_user)

        login_user(new_user)

        return redirect(get_next_page())

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user is not None:

            if user.check_password(form.password.data):
                login_user(user)
                return redirect(get_next_page())
            else:
                login_failed()
        else:
            login_failed()

    # This functionality stems from someone attempting to register an email that's already in use.
    # Uses session to pass the email to the login page.
    if 'login_email' in session:
        form.email.data = session['login_email']
        session.pop('login_email', None)

    return render_template("login.html", form=form)


@app.route('/logout', methods=['GET'])
def logout():

    # If we're not logged in, redirect to main page.
    # Wouldn't make sense to logout when already logged out.
    if not is_logged_in():
        return redirect(get_next_page())

    logout_user()

    return redirect(get_next_page())


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):

    form = CommentForm()

    if form.validate_on_submit() and is_logged_in():

        new_comment = Comment(
            text=form.comment.data,
            author_id=current_user.id,
            post_id=post_id
        )

        db.session.add(new_comment)
        db.session.commit()

        return redirect(url_for('show_post', post_id=post_id))

    requested_post = db.session.query(BlogPost).get(post_id)

    return render_template("post.html", post=requested_post, form=form)


@app.route("/about")
def about():

    return render_template("about.html")


@app.route("/contact")
def contact():

    return render_template("contact.html")


@app.route("/new-post", methods=['GET', 'POST'])
@login_required
@admin_only
def add_new_post(*args, **kwargs):

    form = CreatePostForm()
    if form.validate_on_submit():

        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )

        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>")
@login_required
@admin_only
def edit_post(*args, **kwargs):

    post = db.session.query(BlogPost).get(args[1]['post_id'])

    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():

        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data

        db.session.commit()

        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(*args, **kwargs):

    post = db.session.query(BlogPost).get(args[1]['post_id'])
    if current_user.id == 1 or post.author.id == current_user.id:
        delete_item(post)

    return redirect(url_for('get_all_posts'))


@app.route("/delete-comment/<int:post_id>/<int:comment_id>")
@login_required
def delete_comment(post_id, comment_id):

    comment = db.session.query(Comment).get(comment_id)
    if current_user.id == 1 or comment.author.id == current_user.id:
        delete_item(comment)

    return redirect(url_for('show_post', post_id=post_id))
