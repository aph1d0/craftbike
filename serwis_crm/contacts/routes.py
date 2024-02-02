from flask_login import current_user, login_required
from flask import render_template, flash, url_for, redirect, request, Blueprint, session
import json
from wtforms import Label
from sqlalchemy import or_, text
from datetime import date, timedelta

from serwis_crm import db
from .models import Contact
from serwis_crm.common.paginate import Paginate
from serwis_crm.common.filters import CommonFilters
from .forms import NewContact, FilterContacts, filter_contacts_adv_filters_query
from serwis_crm.users.utils import upload_avatar

from serwis_crm.rbac import check_access

contacts = Blueprint('contacts', __name__)
    
def set_filters(f_id, module):
    today = date.today()
    filter_d = True
    if f_id == 1:
        filter_d = text("Date(%s.date_created)='%s'" % (module, today))
    elif f_id == 2:
        filter_d = text("Date(%s.date_created)='%s'" % (module, (today - timedelta(1))))
    elif f_id == 3:
        filter_d = text("Date(%s.date_created) > current_date - interval '7' day" % module)
    elif f_id == 4:
        filter_d = text("Date(%s.date_created) > current_date - interval '30' day" % module)
    return filter_d


def set_date_filters(filters, module, key):
    filter_d = True
    if request.method == 'POST':
        if filters.advanced_user.data:
            filter_d = set_filters(filters.advanced_user.data['id'], module)
            session[key] = filters.advanced_user.data['id']
        else:
            session.pop(key, None)
    else:
        if key in session:
            filter_d = set_filters(session[key], module)
            filters.advanced_user.data = filter_contacts_adv_filters_query()[session[key] - 1]
    return filter_d


def reset_contacts_filters():
    if 'contacts_owner' in session:
        session.pop('contacts_owner', None)
    if 'contacts_search' in session:
        session.pop('contacts_search', None)
    if 'contacts_date_created' in session:
        session.pop('contacts_date_created', None)


@contacts.route("/contacts", methods=['GET', 'POST'])
@login_required
@check_access('contacts', 'view')
def get_contacts_view():
    filters = FilterContacts()
    search = CommonFilters.set_search(filters, 'contacts_search')
    owner = CommonFilters.set_owner(filters, 'Contact', 'contacts_owner')
    advanced_filters = set_date_filters(filters, 'Contact', 'contacts_date_created')

    query = Contact.query.filter(or_(
            Contact.first_name.ilike(f'%{search}%'),
            #Contact.last_name.ilike(f'%{search}%'),
            Contact.phone.ilike(f'%{search}%'),
        ) if search else True)\
        .filter(owner) \
        .filter(advanced_filters) \
        .order_by(Contact.date_created.desc())

    return render_template("contacts/contacts_list.html", title="Przegląd klientów",
                           contacts=Paginate(query=query), filters=filters)

@contacts.route("/contacts/new", methods=['GET', 'POST'])
@login_required
@check_access('contacts', 'create')
def new_contact(first_name, phone, current_user):
    contact = Contact(
            phone=phone,
            first_name=first_name)
    contact.owner_id = current_user
    db.session.add(contact)
    db.session.commit()
    return contact

@contacts.route("/contacts/edit/<int:contact_id>", methods=['GET', 'POST'])
@login_required
@check_access('contacts', 'update')
def update_contact(contact_id):
    contact = Contact.get_contact(contact_id)
    if not contact:
        return redirect(url_for('contacts.get_contacts_view'))

    form = NewContact()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            contact.first_name = form.first_name.data
            #contact.last_name = form.last_name.data
            contact.phone = form.phone.data
            contact.notes = form.notes.data
            db.session.commit()
            flash('Klient zaktualizowany!', 'success')
            return redirect(url_for('contacts.get_contact_view', contact_id=contact.id))
        else:
            print(form.errors)
            flash('Contact update failed! Form has errors', 'danger')
    elif request.method == 'GET':
        form.first_name.data = contact.first_name
        #form.last_name.data = contact.last_name
        form.phone.data = contact.phone
        form.assignees.data = contact.contact_owner
        form.notes.data = contact.notes
        form.submit.label = Label('update_contact', 'Aktualizuj klienta')
    return render_template("contacts/new_contact.html", title="AKtualizuj klienta", form=form)


@contacts.route("/contacts/<int:contact_id>")
@login_required
@check_access('contacts', 'view')
def get_contact_view(contact_id):
    contact = Contact.query.filter_by(id=contact_id).first()
    return render_template("contacts/contact_view.html", title="Przegląd klienta", contact=contact)


@contacts.route("/contacts/del/<int:contact_id>")
@login_required
@check_access('contacts', 'delete')
def delete_contact(contact_id):
    Contact.query.filter_by(id=contact_id).delete()
    db.session.commit()
    flash('Contact removed successfully!', 'success')
    return redirect(url_for('contacts.get_contacts_view'))


@contacts.route("/contacts/reset_filters")
@login_required
@check_access('contacts', 'view')
def reset_filters():
    reset_contacts_filters()
    return redirect(url_for('contacts.get_contacts_view'))
