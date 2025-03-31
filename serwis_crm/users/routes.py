from flask import Blueprint, session
from flask_login import current_user, login_user, logout_user
from flask import render_template, flash, url_for, redirect, request

from serwis_crm import db, bcrypt
from .forms import Register, Login
from .models import User
from serwis_crm.rbac import check_access

users = Blueprint('users', __name__)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = Login()
    if request.method == 'POST':
        #if form.is_submitted() and form.validate():
        if form.is_submitted() and form.validate():
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                if not user.is_user_active:
                    flash("""User has not been granted access to the system!
                          Please contact the system administrator""",
                          'danger')
                elif not bcrypt.check_password_hash(user.password, form.password.data):
                    flash('Invalid Password!', 'danger')
                else:
                    login_user(user, remember=form.remember.data)
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('main.home'))
            else:
                flash('User does not exist! Please contact the system administrator', 'danger')
    return render_template("login.html", title="serwis_crm - Login", form=form)



@users.route("/logout")
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('users.login'))


