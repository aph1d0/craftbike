from flask import render_template, flash, session, url_for, redirect, Blueprint, current_app
from serwis_crm import db
from flask_login import login_required, current_user
from configparser import ConfigParser
from sqlalchemy import or_
from serwis_crm.common.filters import CommonFilters
from serwis_crm.leads.filters import set_date_filters
from serwis_crm.leads.forms import FilterLeads
from serwis_crm.leads.models import LeadMain, LeadStatus
from serwis_crm.rbac import check_access
from datetime import datetime, timedelta

parser = ConfigParser()

main = Blueprint('main', __name__)

def reset_main_filters():
    if 'lead_owner' in session:
        session.pop('lead_owner', None)
    if 'lead_search' in session:
        session.pop('lead_search', None)
    if 'lead_date_created' in session:
        session.pop('lead_date_created', None)
    if 'lead_contact' in session:
        session.pop('lead_contact', None)

def cleanup_old_session_data():
    """Clean up session data older than 24 hours"""
    if 'lead_owner' in session:
        session.pop('lead_owner', None)
    if 'lead_search' in session:
        session.pop('lead_search', None)
    if 'lead_date_created' in session:
        session.pop('lead_date_created', None)
    if 'lead_contact' in session:
        session.pop('lead_contact', None)
    session.permanent = True
    current_app.permanent_session_lifetime = timedelta(hours=24)

@main.before_request
def before_request():
    cleanup_old_session_data()

@main.route("/_health", methods=['GET'])
def health_check():
    return '', 200

@main.route("/")
@main.route("/home", methods=['GET', 'POST'])
@check_access('leads', 'view')
@login_required
def home():
    filters = FilterLeads()
    search = CommonFilters.set_search(filters, 'lead_search')
    owner = CommonFilters.set_owner(filters, 'lead_main', 'lead_owner')
    contact = CommonFilters.set_contacts(filters, 'lead_main', 'lead_contact')
    advanced_filters = set_date_filters(filters, 'lead_date_created')
    good_leads = []
    statuses = LeadStatus.query.filter(LeadStatus.status_name != "Odebrany", LeadStatus.status_name != "Sprzedany").all()
    leads = LeadMain.query \
        .filter(or_(
            LeadMain.title.ilike(f'%{search}%'),
        ) if search else True) \
        .filter(contact) \
        .filter(owner) \
        .filter(advanced_filters) \
    .all()
    for lead in leads:
        if lead.status.status_name == "Przyjęty na serwis" \
            or lead.status.status_name == "Umówiony na serwis" \
            or lead.status.status_name == "Gotowy" \
            or lead.status.status_name == "Na sprzedaż":
            lead.date_scheduled = lead.date_scheduled.strftime("%Y-%m-%d")
            good_leads.append(lead)
            
    return render_template("index.html", title="Dashboard", leads=good_leads, lead_statuses=statuses, filters=filters)

@main.route("/calendar", methods=['GET'])
@check_access('leads', 'view')
@login_required
def calendar():
    return render_template("calendar.html", title="Kalendarz")

@main.route("/home/reset_filters")
@check_access('leads', 'view')
@login_required
def reset_filters():
    reset_main_filters()
    return redirect(url_for('main.home'))

@login_required
@main.route("/create_db")
def create_db():
    db.create_all()
    flash('Database created successfully!', 'info')
    return redirect(url_for('main.home'))


@current_app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', title="Oops! Page Not Found", error=error), 404
