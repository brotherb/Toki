from flask.ext.wtf import Form, TextField, BooleanField, required,\
    TextAreaField, PasswordField, Length, EqualTo, Email, ValidationError
from models import User
from flask.ext.babel import lazy_gettext as _


required_error = _('This field is required')


class RegisterForm(Form):
    name = TextField(_('Username'), [required(required_error), Length(max=32, message=_('Uername too long!'))])
    password = PasswordField(_('Password'), [required(required_error), Length(min=8, max=32, message=_('Password too long or too short!'))])
    confirm_password = PasswordField(_('Confirm password'), [required(required_error), EqualTo('password', message=_('Password do not match!'))])
    email = TextField(_('Email'), [required(required_error), Email(message=_('Invalid Email address'))])

    def validate_name(form, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError(_('Username has been taken!'))
        return False

    def validate_email(form, field):
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError(_('Email address has been taken!'))
        return False


class LoginForm(Form):
    account = TextField(_('Account'), [required(required_error)])
    password = PasswordField(_('Password'), [required(required_error)])
    remember_me = BooleanField(_('Remember me'), default=False)


class CreateForm(Form):
    title = TextField('', [required(required_error)])
    body = TextAreaField('', [required(required_error)])
    tags = TextField('', [required(required_error)])


class EditForm(Form):
    body = TextAreaField('', [required(required_error)])
    commit_msg = TextField('', [required(required_error)])


class SearchForm(Form):
    term = TextField('', [required(required_error)])
