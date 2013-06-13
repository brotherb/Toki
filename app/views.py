from app import app, lm, db, babel
from config import LANGUAGES
from flask import render_template, request, flash, redirect, url_for, g, abort
from flask.ext.login import login_user, login_required, current_user, logout_user
from flask.ext.babel import gettext as _
from forms import LoginForm, CreateForm, EditForm, SearchForm, RegisterForm
from models import User, STATUS_WAITING_FOR_CONFIRM, STATUS_ACTIVE, Mark, Page, Tag, Score
from helpers import pm, um, convertMarkdown
import mailing
from math import ceil
import hashlib


items_per_page = 15


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user


@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        u = um.add_user(form.name.data, form.password.data, form.email.data)
        mailing.send_awaiting_confirm_mail(u)
        flash(_('We have sent you confirm message, please check your Email~'))
        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user1 = User.query.filter(User.username == form.account.data).first()
        user2 = User.query.filter(User.email == form.account.data).first()
        if user1 is None:
            user = user2
        else:
            user = user1
        if user is None:
            flash(_('Username/Email does not exist'))
        elif user.status == STATUS_WAITING_FOR_CONFIRM:
            flash(_('User is Inactive, Please check your email'))
        else:
            code = hashlib.md5()
            code.update(form.password.data+user.username)
            print code.hexdigest()
            if code.hexdigest() != user.password:
                flash(_('Password is not correct'))
            else:
                login_user(user, remember=form.remember_me.data)
                return redirect(url_for('home'))
    return render_template('login.html', form=form)


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/', methods=['GET', 'POST'])
def home():
    # page = Wiki.get('home')
    # if page:
    #     return display('home')
    return render_template('home.html')


@app.route('/index/')
def index():
    page_num = int(request.args.get('page_num', 1))
    sum = int(ceil(len(Page.query.all())*1.0/items_per_page))
    if page_num < 1 or page_num > sum:
        abort(404)
    pages = pm.get_page_index(page_num)
    return render_template('index.html', pages=pages, page_num=page_num, sum=sum)


@app.route('/create/', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateForm()

    if form.validate_on_submit():
        page = pm.save_new_page(form.title.data, content=form.body.data, tags=form.tags.data)
        flash(_('Page created.'), 'success')
        return redirect(url_for('show', id=page.id))
    return render_template("editor.html", form=form, title=_('create a new page'), flag='Create', highlight=True)


@app.route('/edit/<int:id>/', methods=['GET', 'POST'])
@login_required
def edit(id):
    page, content = pm.get_page_and_content(id)
    if not page:
        abort(404)
    form = EditForm(body=content.text)

    if form.validate_on_submit():
        pm.save_modified_page(page, content=form.body.data, commitMSG=form.commit_msg.data)
        pm.set_notification(page)
        flash(_('Page modified.'), 'success')
        return redirect(url_for('show', id=page.id))
    return render_template("editor.html", form=form, title=_('edit')+page.title, flag="Modify")


@app.route('/wiki/<int:id>/')
def show(id):
    page, content = pm.get_page_and_content(id)
    if page.scorer_num == 0:
        percentages = [0.0, 0.0, 0.0, 0.0, 0.0]
    else:
        percentages = [
            page.score_5*100.0/page.scorer_num,
            page.score_4*100.0/page.scorer_num,
            page.score_3*100.0/page.scorer_num,
            page.score_2*100.0/page.scorer_num,
            page.score_1*100.0/page.scorer_num
        ]
    if not page:
        abort(404)
    marked = None
    myscore = None
    if not current_user.is_anonymous():
        marked = Mark.query.filter_by(page_id=id).filter_by(user_id=current_user.id).first()
        myscore = Score.query.filter_by(page_id=id).filter_by(user_id=current_user.id).first()
        if marked:
            marked.notify = False
            db.session.commit()

    return render_template('page.html', page=page, content=content, marked=marked, myscore=myscore,
                           percentages=percentages)


@app.route('/preview/', methods=['POST'])
def preview():
    a = request.form
    return convertMarkdown(a['body'])


@app.route('/delete/<int:id>/')
@login_required
def delete(id):
    page = pm.get_page(id)
    if not page:
        abort(404)
    pm.delete(page)
    flash(_('Page deleted.'), 'success')
    return redirect(url_for('home'))


@app.route('/tags/')
def tags():
    page_num = int(request.args.get('page_num', 1))
    sum = int(ceil(len(Tag.query.all())*1.0/items_per_page))
    if page_num < 1 or page_num > sum:
        abort(404)
    tags = pm.get_tag_index(page_num)
    return render_template('tags.html', tags=tags, page_num=page_num, sum=sum)


@app.route('/tag/<int:id>/')
def tag(id):
    tag = pm.get_tag(id)
    page_num = int(request.args.get('page_num', 1))
    sum = int(ceil(len(tag.pages)*1.0/items_per_page))
    if page_num < 1 or page_num > sum:
        abort(404)
    tagged = pm.index_by_tag(tag, page_num)
    return render_template('tag.html', pages=tagged, tag=tag.name, page_num=page_num, sum=sum, id=id)


@app.route('/history/<int:id>')
def history(id):
    page = pm.get_page(id)
    commitSHA = request.args.get('commitSHA', None)
    if commitSHA:
        version = request.args.get('version', None)
        content = pm.get_version(id, commitSHA)
        return render_template('version.html', page=page, content=content, version=version, commitSHA=commitSHA)
    logs = pm.get_page_logs(id)
    return render_template('history.html', page=page, logs=logs)


@app.route('/checkout/<int:id>')
def checkout(id):
    commitSHA = request.args.get('commitSHA', None)
    version = request.args.get('version', None)
    if commitSHA:
        pm.checkout(id, commitSHA, version)
    flash(_('Revert successfully.'), 'success')
    return redirect(url_for('show', id=id))


@app.route('/search/', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = pm.search(form.term.data)
        return render_template('search.html', results=results, form=form, search=form.term.data)
    return render_template('search.html', form=form)


@app.route('/lock/<int:id>', methods=['POST'])
def lock(id):
    pm.lock(id)
    return "hello,world"


@app.route('/unlock/<int:id>', methods=['POST'])
def unlock(id):
    pm.unlock(id)
    return "hello,world"


@app.route('/mark/<int:id>', methods=['POST'])
def mark(id):
    pm.mark(id, current_user.id)
    return 'hello,world'


@app.route('/unmark/<int:id>', methods=['POST'])
def unmark(id):
    pm.unmark(id, current_user.id)
    return 'hello,world'


@app.route('/score/<int:page_id>/<int:score>', methods=['POST'])
def score(page_id, score):
    pm.score(page_id, current_user.id, score)
    return 'hello,world'


@app.route('/activate_user/<int:user_id>')
def activate_user(user_id):
    """
    Activate user function.
    """
    found_user = User.query.get(user_id)
    if not found_user:
        return abort(404)
    else:
        if found_user.status == STATUS_WAITING_FOR_CONFIRM:
            found_user.status = STATUS_ACTIVE
            db.session.commit()
            mailing.send_subscription_confirmed_mail(found_user)
            flash(_('User has been activated'), 'info')
        return redirect(url_for('login'))


@app.route('/user/<int:id>/marks/')
def my_marks(id):
    modified_only = request.args.get('modified_only', False)
    if modified_only == "True":
        marks = pm.get_marks(id, True)
    else:
        marks = pm.get_marks(id)
    page_num = int(request.args.get('page_num', 1))
    sum = int(ceil(len(marks)*1.0/items_per_page))
    if page_num < 1 or page_num > sum:
        abort(404)
    start = items_per_page*(page_num-1)
    end = items_per_page*page_num
    if end > len(marks):
        end = len(marks)
    return render_template('user_marks.html', marks=marks[start:end], page_num=page_num, sum=sum, id=id,
                           all=(modified_only != "True"))


@app.route('/user/<int:id>/recommendations/')
def recommendation(id):
    pass