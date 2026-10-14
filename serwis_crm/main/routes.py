from flask import render_template, flash, session, url_for, redirect, request, Blueprint, current_app
from serwis_crm import db
from flask_login import login_required, current_user
from configparser import ConfigParser
from sqlalchemy import or_
from serwis_crm.common.filters import CommonFilters
from serwis_crm.leads.filters import set_date_filters
from serwis_crm.leads.forms import FilterLeads
from serwis_crm.leads.models import LeadMain, LeadStatus, \
    DASHBOARD_STATUSES, LOANED_STATUSES
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

def build_kanban_board(status_names):
    """Zbiera kolumny i zlecenia dla widoku kanban o podanych statusach."""
    filters = FilterLeads()
    search = CommonFilters.set_search(filters, 'lead_search')
    owner = CommonFilters.set_owner(filters, 'lead_main', 'lead_owner')
    contact = CommonFilters.set_contacts(filters, 'lead_main', 'lead_contact')
    advanced_filters = set_date_filters(filters, 'lead_date_created')
    statuses = LeadStatus.query \
        .filter(LeadStatus.status_name.in_(status_names)) \
        .order_by(LeadStatus.id.asc()) \
        .all()
    # zachowaj kolejnosc kolumn zdefiniowana w status_names
    statuses.sort(key=lambda s: status_names.index(s.status_name))
    leads = LeadMain.query \
        .join(LeadStatus, LeadMain.lead_status_id == LeadStatus.id) \
        .filter(LeadStatus.status_name.in_(status_names)) \
        .filter(or_(
            LeadMain.title.ilike(f'%{search}%'),
        ) if search else True) \
        .filter(contact) \
        .filter(owner) \
        .filter(advanced_filters) \
    .all()
    today = datetime.now().date()
    # Calculate next Friday. weekday() returns 0 for Monday to 6 for Sunday
    days_ahead = 4 - today.weekday()
    if days_ahead <= 0: # Target is next week
        days_ahead += 7
    next_friday = today + timedelta(days_ahead)

    for lead in leads:
        lead.date_scheduled = lead.date_scheduled.strftime("%Y-%m-%d") if lead.date_scheduled else ''
        lead.priority = 2 # Normal priority by default

        if lead.deadline:
            if lead.deadline < today:
                lead.priority = 0 # High priority (crossed deadline)
            elif lead.deadline <= next_friday:
                lead.priority = 1 # Medium priority (upcoming deadline until next Friday)

    leads.sort(key=lambda x: (x.priority, x.deadline or datetime.max.date()))

    return leads, statuses, filters


@main.route("/")
@main.route("/home", methods=['GET', 'POST'])
@check_access('leads', 'view')
@login_required
def home():
    leads, statuses, filters = build_kanban_board(DASHBOARD_STATUSES)
    return render_template("index.html", title="Dashboard", leads=leads, lead_statuses=statuses, filters=filters)


@main.route("/loaned", methods=['GET', 'POST'])
@check_access('leads', 'view')
@login_required
def loaned():
    leads, statuses, filters = build_kanban_board(LOANED_STATUSES)
    return render_template("loaned.html", title="Pożyczone, umówione", leads=leads,
                           lead_statuses=statuses, filters=filters)

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
    next_view = request.args.get('next')
    if next_view not in ('main.home', 'main.loaned'):
        next_view = 'main.home'
    return redirect(url_for(next_view))

@login_required
@main.route("/create_db")
def create_db():
    db.create_all()
    flash('Database created successfully!', 'info')
    return redirect(url_for('main.home'))


@current_app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', title="Oops! Page Not Found", error=error), 404
