from app import db, models
from app.models import ROLE_ADMIN, ROLE_USER

#u = models.User(username='admin', password='admin', email='1078039894@qq.com', role=ROLE_ADMIN)
u = models.User(username='jack', password='jack', email='jackslowfuck@qq.com', role=ROLE_USER)
db.session.add(u)
db.session.commit()
