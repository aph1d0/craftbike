from flask import render_template, session, url_for, redirect, Blueprint, request
from sqlalchemy import text
from serwis_crm import db, bcrypt
import os
import sys
from flask import current_app
from tzlocal import get_localzone

from serwis_crm.settings.models import Currency, TimeZone, AppConfig
from serwis_crm.leads.models import LeadStatus, LeadMain
from serwis_crm.users.models import Role, Resource, User

from serwis_crm.install.forms import NewSystemUser, CurrencyTz, FinishInstall
from serwis_crm.install.data.currency_timezone import INSERT_SQL

install = Blueprint('install', __name__)

@install.route("/_health", methods=['GET'])
def health_check():
    return '', 200

@install.route("/", methods=['GET', 'POST'])
@install.route("/install", methods=['GET', 'POST'])
def sys_info():

    # create empty tables
    db.create_all()

    v = tuple(sys.version.split('.'))
    if v and int(v[0]) < 3 and int(v[1]) < 5:
        return render_template("install/error.html", title="Eeazy CRM installation failed",
                               reason=f"Python version >= {current_app.config['PYTHON_VER_MIN_REQUIRED']} is required for serwis_crm")
    env_vars = {
        'email_user': True if os.getenv('EMAIL_USER') else False,
        'email_pass': True if os.getenv('EMAIL_PASS') else False
    }
    return render_template("install/sys_info.html", title="System Information",
                           system_info=os.uname(), py_ver=sys.version, env_vars=env_vars)


@install.route("/install/sys_user", methods=['GET', 'POST'])
def setup_sys_user():
    form = NewSystemUser()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            session['admin_first_name'] = form.first_name.data
            session['admin_last_name'] = form.last_name.data
            session['admin_email'] = form.email.data
            session['admin_password'] = hashed_pwd

            # create currency & timezone data
            db.session.execute(text(INSERT_SQL))
            db.session.commit()

            return redirect(url_for('install.ex_settings'))
    return render_template("install/sys_user.html", title="Create System User (admin)",
                           form=form)


@install.route("/install/extra_settings", methods=['GET', 'POST'])
def ex_settings():
    # insert currency & timezone tables with data
    form = CurrencyTz()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            session['app_currency_name'] = form.currency.data.name + f'({form.currency.data.symbol})' if form.currency.data.symbol else ''
            session['app_currency_id'] = form.currency.data.id
            session['app_tz_name'] = form.time_zone.data.name
            session['app_tz_id'] = form.time_zone.data.id
            return redirect(url_for('install.finish'))
    elif request.method == 'GET':
        form.currency.data = Currency.get_currency_by_id(142)
        local_tz = get_localzone()
        if local_tz:
            form.time_zone.data = TimeZone.get_tz_by_name(str(local_tz))
        else:
            form.time_zone.data = TimeZone.get_tz_by_id(380)
    return render_template("install/extra_settings.html", title="Set Currency & TimeZone", form=form)


def empty_setup():
    # create system roles & resources
    role = Role(name='general')
    role.resources.append(
        Resource(
            name='staff',
            can_view=True,
            can_edit=False,
            can_create=False,
            can_delete=False
        )
    )

    role.resources.append(
        Resource(
            name='leads',
            can_view=True,
            can_edit=True,
            can_create=True,
            can_delete=True
        )
    )

    role.resources.append(
        Resource(
            name='bikes',
            can_view=True,
            can_edit=True,
            can_create=True,
            can_delete=False
        )
    )

    role.resources.append(
        Resource(
            name='contacts',
            can_view=True,
            can_edit=True,
            can_create=True,
            can_delete=False
        )
    )

    role.resources.append(
        Resource(
            name='services',
            can_view=True,
            can_edit=True,
            can_create=True,
            can_delete=True
        )
    )

    # create user
    user = User(first_name=session['admin_first_name'],
                last_name=session['admin_last_name'],
                email=session['admin_email'],
                password=session['admin_password'],
                is_admin=True,
                is_first_login=True,
                is_user_active=True
                )
    
    status_1 = LeadStatus(id=1, status_name='Przyjęty na serwis', is_final=False)
    db.session.add(status_1)
    status_2 = LeadStatus(id=2, status_name='Umówiony na serwis', is_final=False)
    db.session.add(status_2)
    status_5 = LeadStatus(id=5, status_name='Gotowy', is_final=True)
    db.session.add(status_5)
    status_6 = LeadStatus(id=6, status_name='Odebrany', is_final=True)
    db.session.add(status_6)
    db.session.add(role)
    db.session.add(user)



@install.route("/install/finish", methods=['GET', 'POST'])
def finish():
    form = FinishInstall()
    data = {
        'def_currency': session['app_currency_name'],
        'def_tz': session['app_tz_name']
    }
    if request.method == 'POST':
        if form.is_submitted() and form.validate():

            empty_setup()

            # create configuration
            app_cfg = AppConfig(
                default_currency=session['app_currency_id'],
                default_timezone=session['app_tz_id']
            )

            print(session['app_currency_id'])

            # create application config
            db.session.add(app_cfg)
            db.session.commit()

            return render_template("install/complete.html", title="Hurray! Installation Complete!")
    return render_template("install/finish.html", title="We're all set! Let's finish Installation",
                           data=data, form=form)


@current_app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('install.sys_info'))

