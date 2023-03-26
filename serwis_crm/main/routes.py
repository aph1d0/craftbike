from datetime import date
from flask import render_template, flash, url_for, redirect, Blueprint, current_app
from serwis_crm import db
from flask_login import login_required
from configparser import ConfigParser
from sqlalchemy import or_
from serwis_crm.leads.models import LeadMain, LeadStatus

parser = ConfigParser()

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
@login_required
def home():
    good_leads = []
    statuses = LeadStatus.query.filter(LeadStatus.status_name != "Odebrany").all()
    leads = LeadMain.query.all()
    for lead in leads:
        if lead.status.status_name != "Odebrany" and lead.date_scheduled.date() <= date.today():
            good_leads.append(lead)
    return render_template("index.html", title="Dashboard", leads=good_leads, lead_statuses=statuses)


@main.route("/create_db")
def create_db():
    db.create_all()
    flash('Database created successfully!', 'info')
    return redirect(url_for('main.home'))


@current_app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', title="Oops! Page Not Found", error=error), 404


@current_app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", title="Page Not Found")

