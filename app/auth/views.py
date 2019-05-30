from flask import render_template, redirect, flash, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm
from .. import db

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('Login or password is incorrect')
    return render_template('auth/login.html', form=form)

@auth.route('/secret')
@login_required
def secret():
    return 'Only the choosen one can read this message!'

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            username=form.username.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        flash('You can now login.')
        con_addr = url_for('auth.confirm', token=token, _external=True)
        return f'<a href="{con_addr}">{con_addr}<\a>'
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account, thanks.')
    else:
        flash('Invalid confirmation link')
    return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
        and request.blueprint != 'auth' \
        and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/reconfirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    con_addr = url_for('auth.confirm', token=token, _external=True)
    return f'<a href="{con_addr}">{con_addr}<\a>'
