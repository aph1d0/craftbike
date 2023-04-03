from datetime import date
import datetime
import boto3
import pandas as pd
from sqlalchemy import Date, cast, or_
from wtforms import Label

from flask import Blueprint, jsonify, session, Response
from flask_login import current_user, login_required
from flask import render_template, flash, url_for, redirect, request

from serwis_crm import config, db
from serwis_crm.bikes.models import Bike
from serwis_crm.bikes.routes import new_bike
from serwis_crm.users.models import User
from serwis_crm.leads.models import LeadMain, LeadStatus
from serwis_crm.services.models import ServicesCategory, ServicesAction
from serwis_crm.contacts.models import Contact
from serwis_crm.contacts.routes import new_contact
from serwis_crm.common.paginate import Paginate
from serwis_crm.common.filters import CommonFilters
from .filters import set_date_filters, set_status
from .forms import EditLead, NewLead, ImportLeads, \
    FilterLeads, BulkOwnerAssign, BulkLeadStatusAssign, BulkDelete
from .sms_notification import SnsWrapper

from serwis_crm.rbac import check_access, is_admin

leads = Blueprint('leads', __name__)

def reset_lead_filters():
    if 'lead_owner' in session:
        session.pop('lead_owner', None)
    if 'lead_search' in session:
        session.pop('lead_search', None)
    if 'lead_date_created' in session:
        session.pop('lead_date_created', None)
    if 'lead_status' in session:
        session.pop('lead_status', None)


@leads.route("/leads", methods=['GET', 'POST'])
@login_required
@check_access('leads', 'view')
def get_leads_view():
    filters = FilterLeads()
    search = CommonFilters.set_search(filters, 'lead_search')
    owner = CommonFilters.set_owner(filters, 'lead_main', 'lead_owner')
    advanced_filters = set_date_filters(filters, 'lead_date_created')
    status_filter = set_status(filters, 'lead_status')
    lead=LeadMain.get_by_id(1)

    query = LeadMain.query \
        .join(Contact, LeadMain.contact_id==Contact.id)\
        .join(User, LeadMain.owner_id==User.id)\
        .join(Bike, LeadMain.bike_id==Bike.id)\
        .join(LeadStatus, LeadMain.lead_status_id==LeadStatus.id)\
        .add_columns(LeadMain.id, LeadMain.title, Contact.first_name, Contact.last_name, Contact.phone, Bike.manufacturer, Bike.model, LeadMain.owner_id, User, LeadStatus.status_name, LeadMain.date_created)\
        .filter(or_(
            LeadMain.title.ilike(f'%{search}%'),
            Contact.phone.ilike(f'%{search}%'),
            Contact.first_name.ilike(f'%{search}%'),
            Contact.last_name.ilike(f'%{search}%'),
            Bike.manufacturer.ilike(f'%{search}%'),
            Bike.model.ilike(f'%{search}%')
        ) if search else True) \
        .filter(status_filter) \
        .filter(owner) \
        .filter(advanced_filters) \
        .order_by(LeadMain.date_created.desc())

    bulk_form = {
        'owner': BulkOwnerAssign(),
        'lead_status': BulkLeadStatusAssign(),
        'delete': BulkDelete()
    }

    return render_template("leads/leads_list.html", title="Widok zleceń serwisowych",
                           leads=Paginate(query), filters=filters, bulk_form=bulk_form)

@login_required
@check_access('leads', 'update')
@leads.route('/leads/update_stage/<int:lead_id>/<int:lead_stage_id>', methods=['GET','POST'])
def update_stage(lead_id, lead_stage_id):
    lead = LeadMain.query.filter(LeadMain.id == lead_id).first()
    owner = User.get_current_user()
    lead_stage = LeadStatus.get_by_id(lead_stage_id)
    # to disable dragging back and forth from final stage
    if lead_stage.is_final == False and lead.status.is_final == True:
        error = {'message': 'Nie można zaktualizować statusu zlecenia w tę strone!', 'status': 500}
        response  = jsonify(error)
        response.status_code = error['status']
        return response
    if lead_stage_id == 5:
        try:
            sns = boto3.resource('sns')
            sms_notif = SnsWrapper(sns)
            message = "Dzień dobry! Tu serwis rowerowy CraftBike. Twój rower jest już gotowy do odbioru. Zapraszamy do naszego serwisu w tygodniu 10-18 oraz w soboty 10-14."
            sms_notif.publish_text_message(phone_number=lead.lead_contact.phone, message=message)
        except:
            error = {'message': 'Coś nie poszło z wysyłaniem tego typu smsa :<', 'status': 500}
            response  = jsonify(error)
            response.status_code = error['status']
            return response
    lead.owner = owner
    lead.lead_status_id = lead_stage_id
    db.session.add(lead)
    db.session.commit()
    ok = {'message': 'Zaktualizowano status zlecenia poprawnie.', 'status': 200}
    response  = jsonify(ok)
    response.status_code = ok['status']
    return response

@login_required
@check_access('leads', 'view')
@leads.route("/leads/<int:lead_id>/get_services", methods=['GET'])
def get_services(lead_id):
    json_services = []
    lead = LeadMain.query.filter(LeadMain.id == lead_id).first()
    for service in lead.services:
        json_services.append({
            'id' : service.id,
            'name' : service.name,
            'price' : service.price
        }
        )
    return jsonify(json_services)

@login_required
@check_access('leads', 'view')
@leads.route('/leads/new/_autoset_title', methods=['POST'])
def autoset():
    input_1_value = request.form['bike_manufacturer']
    input_2_value = request.form['bike_model']
    # Calculate the new value for input 3 based on input 1 and input 2
    new_value = str(input_1_value) + " " + str(input_2_value)
    return jsonify({'new_value': new_value})

@check_access('leads', 'view')
@login_required
@leads.route('/leads/get_scheduled', methods=['GET'])
def get_scheduled():
    json_scheduled_services = []
    scheduled_services = LeadMain.query.filter(cast(LeadMain.date_scheduled,Date) >= date.today()).all()
    for scheduled_service in scheduled_services:
        json_scheduled_services.append({
            'id' : scheduled_service.id,
            'title' : scheduled_service.title,
            'start' : scheduled_service.date_scheduled.strftime('%Y-%m-%d')
        }
            )
        #a = jsonify(json_scheduled_serwices)
    return json_scheduled_services

# @leads.route("/leads/new/suggest_service", methods=['GET', 'POST'])
# @login_required
# @check_access('leads', 'create')
# def suggest_service():
#     query = request.args.get('query')
#     if not query:
#         return jsonify([])
#     items = Services.query.filter(Services.name.ilike(f'%{query}%')).all()
#     suggestions = [item.name for item in items]
#     return jsonify(suggestions)

# @leads.route("/leads/new/get_service_price", methods=['GET', 'POST'])
# @login_required
# @check_access('leads', 'create')
# def get_service_price():
#     query = request.args.get('query')
#     if not query:
#         return jsonify([])
#     price = Services.query.filter(Services.name == query).first()
#     return jsonify(price.price)

@leads.route("/leads/new", methods=['GET', 'POST'])
@login_required
@check_access('leads', 'create')
def new_lead():
    found_bike = False
    form = NewLead()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            client = Contact.query.filter_by(phone=form.phone.data).first()
            if not client:
                client = new_contact(first_name=form.first_name.data, last_name=form.last_name.data, phone=form.phone.data, current_user=current_user.id)
            clients_bikes = Bike.query.filter_by(contact_id=client.id).all()
            for client_bike in clients_bikes:
                if str(form.bike_manufacturer.data).lower() == client_bike.manufacturer and str(form.bike_model.data).lower() == client_bike.model:
                    bike = client_bike
                    found_bike=True
                    break
            if not found_bike:
                    bike = new_bike(bike_manufacturer=str(form.bike_manufacturer.data).lower(), bike_model=str(form.bike_model.data).lower(), client_id=client.id)
            lead = LeadMain(title=form.title.data,
                        status=form.lead_status.data, notes=form.notes.data)
            # for service in form.service_name.raw_data:
            #     service_obj = Services.query.filter(Services.name == service).first()
            #     if service_obj:
            #         lead.services.append(service_obj)
            if form.lead_status.data.status_name == 'Umówiony na serwis':
                lead.date_scheduled = form.date_scheduled.data
            else:
                lead.date_scheduled = datetime.datetime.now().strftime('%Y-%m-%d')
                
            if current_user.is_admin:
                lead.owner = form.assignees.data
            else:
                lead.owner = current_user
            lead.contact_id = client.id
            lead.bike_id = bike.id
            db.session.add(lead)
            db.session.commit()
            flash('Nowe zlecenie serwisowe utworzone!', 'success')
            return redirect(url_for('leads.get_leads_view'))
        else:
            for error in form.errors:
                print(error)
            flash('Błednie wypełniony formularz. Sprawdz go ponownie baranie!', 'danger')
    return render_template("leads/new_lead.html", title="Nowe zlecenie", form=form)


@leads.route("/leads/edit/<int:lead_id>", methods=['GET', 'POST'])
@login_required
@check_access('leads', 'update')
def update_lead(lead_id):
    lead = LeadMain.get_by_id(lead_id)
    bike = Bike.get_bike(lead.bike_id)
    contact = Contact.get_contact(lead.contact_id)
    if not lead:
        return redirect(url_for('leads.get_leads_view'))

    form = EditLead()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            lead.title = form.title.data
            contact.first_name = form.first_name.data
            contact.last_name = form.last_name.data
            contact.phone = form.phone.data
            bike.manufacturer = form.bike_manufacturer.data
            bike.model = form.bike_model.data
            lead.owner = form.assignees.data
            lead.status = form.lead_status.data
            lead.date_scheduled = form.date_scheduled.data
            lead.notes = form.notes.data
            services = []
            # for service in form.service_name.raw_data:
            #     service_obj = Services.query.filter(Services.name == service).first()
            #     if service_obj:
            #         services.append(service_obj)
            lead.services = services
            up_stage = update_stage(lead_id=lead.id, lead_stage_id=lead.status.id)
            if up_stage.json["status"] == 200:
                db.session.commit()
                flash('Zlecenie uaktualnione poprawnie!', 'success')
                return redirect(url_for('leads.get_lead_view', lead_id=lead.id))
            else:
                flash('Aktualizacja zlecenia nie powiodła się!', 'danger')
        else:
            print(form.errors)
            flash('Aktualizacja zlecenia nie powiodła się! Sprawdź formularz.', 'danger')
    elif request.method == 'GET':
        form.title.data = lead.title
        form.first_name.data = contact.first_name
        form.last_name.data = contact.last_name
        form.phone.data = contact.phone
        form.bike_manufacturer.data = bike.manufacturer
        form.bike_model.data = bike.model
        form.assignees.data = lead.owner
        form.lead_status.data = lead.status
        form.date_scheduled.data = lead.date_scheduled.strftime('%Y-%m-%d')
        form.notes.data = lead.notes
        form.total_price.data = LeadMain.get_total_price(lead.id)
        form.submit.label = Label('update_lead', 'Aktualizuj zlecenie')
    return render_template("leads/new_lead.html", title="Aktualizuj zlecenie", form=form, lead_id=lead.id)


@leads.route("/leads/<int:lead_id>")
@login_required
@check_access('leads', 'view')
def get_lead_view(lead_id):
    lead = LeadMain.query.filter_by(id=lead_id).first()
    lead.date_scheduled= lead.date_scheduled.strftime('%Y-%m-%d')
    bike = Bike.get_bike(lead.bike_id)
    contact = Contact.get_contact(lead.contact_id)
    lead.total_price = LeadMain.get_total_price(lead.id)
    return render_template("leads/lead_view.html", title="Przegląd zlecenia", lead=lead, bike=bike, contact=contact)


@leads.route("/leads/del/<int:lead_id>")
@login_required
@check_access('leads', 'remove')
def delete_lead(lead_id):
    lead = LeadMain.query.filter_by(id=lead_id).first()
    if not lead:
        flash('Zlecenie nie istnieje :(', 'danger')
    else:
        #LeadMain.query.filter_by(id=lead_id).delete()
        lead = LeadMain.query.filter_by(id=lead_id).first()
        for service in lead.services:
            lead.services.remove(service)
        db.session.commit()
        LeadMain.query.filter_by(id=lead_id).delete()
        db.session.commit()
        flash('Zlecenie usunięte poprawnie', 'success')
    return redirect(url_for('leads.get_leads_view'))



@leads.route("/leads/import", methods=['GET', 'POST'])
@login_required
@is_admin
def import_bulk_leads():
    form = ImportLeads()
    if request.method == 'POST':
        ind = 0
        if form.is_submitted() and form.validate():
            data = pd.read_csv(form.csv_file.data)

            for _, row in data.iterrows():
                lead = LeadMain(title=row['title'], contact_id=row['contact_id'],
                            bike_id=row['bike_id'], notes=row['notes'], lead_status_id=row['lead_status_id'],
                            owner_id=row['owner_id'], date_created=row['date_created'], date_scheduled=row['date_scheduled'])
                lead.owner = current_user
                db.session.add(lead)
                ind = ind + 1

            db.session.commit()
            flash(f'{ind} nowych zleceń zostało poprawnie zaimportowanych!', 'success')
        else:
            flash('Błednie wypełniony formularz. Sprawdz go ponownie baranie!', 'danger')
    return render_template("leads/leads_import.html", title="Importuj zlecenia", form=form)


@leads.route("/leads/reset_filters")
@login_required
@check_access('leads', 'view')
def reset_filters():
    reset_lead_filters()
    return redirect(url_for('leads.get_leads_view'))


@leads.route("/leads/bulk_owner_assign", methods=['POST'])
@login_required
@is_admin
def bulk_owner_assign():
    form = BulkOwnerAssign()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            if form.owners_list.data:
                ids = [int(x) for x in request.form['leads_owner'].split(',')]
                LeadMain.query\
                    .filter(LeadMain.id.in_(ids))\
                    .update({
                        LeadMain.owner_id: form.owners_list.data.id
                    }, synchronize_session=False)
                db.session.commit()
                flash(f'Owner has been assigned to {len(ids)} lead(s) successfully!', 'success')
        else:
            print(form.errors)

    return redirect(url_for('leads.get_leads_view'))


@leads.route("/leads/bulk_lead_status_assign", methods=['POST'])
@login_required
@is_admin
def bulk_lead_status_assign():
    form = BulkLeadStatusAssign()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            if form.lead_status_list.data:
                ids = [int(x) for x in request.form['leads_status'].split(',')]
                LeadMain.query \
                    .filter(LeadMain.id.in_(ids)) \
                    .update({
                        LeadMain.lead_status_id: form.lead_status_list.data.id
                    }, synchronize_session=False)
                db.session.commit()
                flash(f'Lead status `{form.lead_status_list.data.status_name}` has been '
                      f'assigned to {len(ids)} lead(s) successfully!', 'success')
        else:
            print(form.errors)
    return redirect(url_for('leads.get_leads_view'))


@leads.route("/leads/bulk_delete", methods=['POST'])
@is_admin
def bulk_delete():
    form = BulkDelete()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            ids = [int(x) for x in request.form['leads_to_delete'].split(',')]
            LeadMain.query \
                .filter(LeadMain.id.in_(ids)) \
                .delete(synchronize_session=False)
            db.session.commit()
            flash(f'Successfully deleted {len(ids)} lead(s)!', 'success')
        else:
            print(form.errors)
    return redirect(url_for('leads.get_leads_view'))


@leads.route("/leads/write_csv")
@login_required
def write_to_csv():
    ids = [int(x) for x in request.args.get('lead_ids').split(',')]
    query = LeadMain.query \
        .filter(LeadMain.id.in_(ids))
    csv = 'Title,contact_id,bike_id,Notes,lead_status_id,' \
          'owner_id,date_created,date_scheduled\n'
    for lead in query.all():
        csv += f'{lead.title},{lead.contact_id},' \
               f'{lead.bike_id},{lead.notes},' \
               f'{lead.lead_status_id},{lead.owner_id},{lead.date_created},' \
               f'{lead.date_scheduled}\n'
    return Response(csv,
                    mimetype='text/csv',
                    headers={"Content-disposition":
                             "attachment; filename=services.csv"})