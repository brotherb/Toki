import os
import subprocess
import markdown
import re
from app import db, app
from models import *
from flask.ext.login import current_user
import hashlib


items_per_page = 15


def convertMarkdown(content):
    md = markdown.Markdown(extensions=['meta', 'codehilite', 'fenced_code'])
    return md.convert(content)


class Content(object):
    def __init__(self, path=None, content=None):
        if path:
            with open(path, 'rU') as f:
                self.text = f.read().decode('utf-8')
        else:
            self.text = content

        self.html = convertMarkdown(self.text)

    def __html__(self):
        return self.html


class PageManager(object):
    #initialize root address
    def __init__(self, root):
        self.root = root

    def path(self, id):
        return os.path.join(self.root, str(id) + '.md')

    #simple get page
    def get_page(self, id):
        return Page.query.get(id)

    def get_tag(self, id):
        return Tag.query.get(id)

    #get page and content
    def get_page_and_content(self, id):
        page = Page.query.get(id)
        if page is None:
            return None, None
        content = Content(path=self.path(id))
        return page, content

    #update page content
    def update_content(self, page, content, commitMSG, OP):
        with open(self.path(page.id), 'w') as f:
            f.write(content.replace('\r\n', os.linesep).encode('utf-8'))
        os.chdir(self.root)
        subprocess.call('git add '+str(page.id)+'.md', shell=True)
        subprocess.call('git commit -m "'+commitMSG+'"', shell=True)
        p = subprocess.Popen('git rev-parse HEAD', shell=True, stdout=subprocess.PIPE)
        commitSHA = p.stdout.read().strip('\n')
        log = Log(current_user, page, OP, commitSHA, commitMSG)
        db.session.add(log)
        db.session.commit()

    #save newly created page
    def save_new_page(self, title, content, tags):
        #save tags and page
        page = Page(title)
        tag_list = tags.split(',')
        for item in tag_list:
            t = Tag.query.filter_by(name=item).first()
            if not t:
                t = Tag(item)
                page.tags.append(t)
                db.session.add(t)
            else:
                page.tags.append(t)
        db.session.add(page)
        db.session.commit()
        #save content on plain text file
        self.update_content(page, content, commitMSG='Page Created Successfully', OP=OP_CREATE)
        return page

    #save modified page
    def save_modified_page(self, page, content, commitMSG):
        page.last_edit_date = datetime.now()
        db.session.commit()
        #simply update page content
        self.update_content(page, content, commitMSG, OP=OP_MODIFY)

    def set_notification(self, page):
        for mark in Mark.query.filter_by(page_id=page.id).filter(Mark.user_id != current_user.id).all():
            mark.notify = True
        db.session.commit()

    #delete page
    def delete(self, page):
        #delete page content
        os.remove(self.path(page.id))
        os.chdir(self.root)
        subprocess.call('git rm '+str(page.id)+'.md', shell=True)
        subprocess.call('git commit -m "Page Deleted Successfully"', shell=True)
        #delete page information and all of the history
        for item in Log.query.filter_by(page_id=page.id):
            db.session.delete(item)
        db.session.delete(page)
        db.session.commit()
        return True

    def get_page_index(self, page_num=None):
        pages = Page.query.all()
        if not page_num:
            return pages
        sum = len(pages)
        start = items_per_page*(page_num-1)
        end = items_per_page*page_num
        if sum < end:
            end = sum
        return pages[start:end]

    def get_tag_index(self, page_num=None):
        tags = Tag.query.all()
        if not page_num:
            return tags
        sum = len(tags)
        start = items_per_page*(page_num-1)
        end = items_per_page*page_num
        if sum < end:
            end = sum
        return tags[start:end]

    def index_by_tag(self, tag, page_num=None):
        if not page_num:
            return tag.pages
        sum = len(tag.pages)
        start = items_per_page*(page_num-1)
        end = items_per_page*page_num
        if sum < end:
            end = sum
        return tag.pages[start:end]

    def get_page_logs(self, id):
        return Log.query.filter_by(page_id=id).order_by(Log.time.desc()).all()

    def get_user_logs(self, id):
        return Log.query.filter_by(user_id=id).all()

    def get_version(self, id, commitSHA):
        os.chdir(self.root)
        p = subprocess.Popen('git show '+commitSHA+':'+str(id)+'.md', shell=True, stdout=subprocess.PIPE)
        return Content(content=p.stdout.read().decode("utf8"))

    def checkout(self, id, commitSHA, version):
        os.chdir(self.root)
        subprocess.call('git checkout '+commitSHA+' '+str(id)+'.md', shell=True)
        subprocess.call('git add '+str(id)+'.md', shell=True)
        commitMSG = 'Switch to version(#%s)' % version
        subprocess.call('git commit -m '+commitMSG, shell=True)
        p = subprocess.Popen('git rev-parse HEAD', shell=True, stdout=subprocess.PIPE)
        commitSHA = p.stdout.read().strip('\n')
        log = Log(current_user, self.get_page(id), OP_CHECKOUT, commitSHA, commitMSG)
        db.session.add(log)
        db.session.commit()

    def search(self, term):
        pages = self.get_page_index()
        regex = re.compile(term)
        matched = []
        for page in pages:
            flag = False
            if regex.search(page.title):
                matched.append(page)
                continue
            for tag in page.tags:
                if regex.search(tag.name):
                    matched.append(page)
                    flag = True
                    break
            if flag:
                continue
            with open(self.path(page.id), 'r') as f:
                content = f.read()
                if regex.search(content):
                    matched.append(page)
        return matched

    def lock(self, id):
        Page.query.get(id).locked = True
        db.session.commit()

    def unlock(self, id):
        Page.query.get(id).locked = False
        db.session.commit()

    def mark(self, page_id, user_id):
        if not Mark.query.filter_by(page_id=page_id).filter_by(user_id=user_id).first():
            m = Mark(page_id=page_id, user_id=user_id, notify=False)
            db.session.add(m)
            db.session.commit()

    def unmark(self, page_id, user_id):
        m = Mark.query.filter_by(page_id=page_id).filter_by(user_id=user_id).first()
        if m:
            db.session.delete(m)
            db.session.commit()

    def get_marks(self, id, modified_only=False):
        if modified_only:
            return Mark.query.filter_by(user_id=id).filter_by(notify=True).all()
        return Mark.query.filter_by(user_id=id).all()

    def score(self, page_id, user_id, score):
        m = Score.query.filter_by(page_id=page_id).filter_by(user_id=user_id).first()
        if m:
            if not m.score == score:
                p = Page.query.get(page_id)
                if m.score == 1:
                    p.score_1 -= 1
                elif m.score == 2:
                    p.score_2 -= 1
                elif m.score == 3:
                    p.score_3 -= 1
                elif m.score == 4:
                    p.score_4 -= 1
                elif m.score == 5:
                    p.score_5 -= 1
                if score == 1:
                    p.score_1 += 1
                elif score == 2:
                    p.score_2 += 1
                elif score == 3:
                    p.score_3 += 1
                elif score == 4:
                    p.score_4 += 1
                elif score == 5:
                    p.score_5 += 1
                p.score_avg = (p.score_avg*p.scorer_num + score - m.score)/p.scorer_num
                m.score = score
                db.session.commit()
        else:
            m = Score(page_id=page_id, user_id=user_id, score=score)
            db.session.add(m)
            p = Page.query.get(page_id)
            p.score_avg = (p.score_avg*p.scorer_num + score)/(p.scorer_num+1)
            p.scorer_num += 1
            if score == 1:
                p.score_1 += 1
            elif score == 2:
                p.score_2 += 1
            elif score == 3:
                p.score_3 += 1
            elif score == 4:
                p.score_4 += 1
            elif score == 5:
                p.score_5 += 1
            db.session.commit()


class UserManager:
    def add_user(self, username, password, email):
        code = hashlib.md5()
        code.update(password+username)
        u = User(username, code.hexdigest(), email)
        db.session.add(u)
        db.session.commit()
        return u

pm = PageManager(app.config.get('CONTENT_DIR'))
um = UserManager()
