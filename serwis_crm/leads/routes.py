import datetime
import boto3
import pandas as pd
from sqlalchemy import or_
from wtforms import Label

from flask import Blueprint, jsonify, session, Response, current_app
from flask_login import current_user, login_required
from flask import render_template, flash, url_for, redirect, request

from serwis_crm import config, db
from serwis_crm.bikes.models import Bike
from serwis_crm.bikes.routes import new_bike
from serwis_crm.users.models import User
from serwis_crm.leads.models import LeadMain, LeadStatus, lead_service
from serwis_crm.services.models import ServicesToLeads, ServicesAction
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

def clean_up_not_attached_services():
    """Clean up orphaned services and related resources"""
    try:
        # Get a list of IDs from the "lead_service" table
        lead_service_ids = [record.service_id for record in db.session.query(lead_service).all()]

        # Delete rows from "services_to_leads" where the ID is not in "lead_service_ids"
        deleted_rows = ServicesToLeads.query.filter(~ServicesToLeads.id.in_(lead_service_ids)).delete(synchronize_session=False)


        # Commit the changes to the database
        db.session.commit()
        
        # Force garbage collection
        import gc
        gc.collect()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during cleanup: {str(e)}")
        raise

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

    query = LeadMain.query \
        .join(Contact, LeadMain.contact_id==Contact.id)\
        .join(User, LeadMain.owner_id==User.id)\
        .join(Bike, LeadMain.bike_id==Bike.id)\
        .join(LeadStatus, LeadMain.lead_status_id==LeadStatus.id)\
        .add_columns(LeadMain.id, LeadMain.title, Contact.phone, LeadMain.sms_sent, Contact.first_name, Bike.manufacturer, Bike.model, LeadMain.owner_id, User, LeadStatus.status_name, LeadMain.date_created)\
        .filter(or_(
            LeadMain.title.ilike(f'%{search}%'),
            Contact.phone.ilike(f'%{search}%'),
            Contact.first_name.ilike(f'%{search}%'),
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
@leads.route('/leads/send_sms/<int:lead_id>', methods=['POST'])
def send_sms(lead_id):
    lead = LeadMain.query.filter(LeadMain.id == lead_id).first()
    lead_stage = LeadStatus.get_by_id(lead.lead_status_id)
    if lead_stage.id == 5 and lead.sms_sending is True and lead.sms_sent is False:
        try:
            sns = boto3.resource('sns')
            sms_notif = SnsWrapper(sns)
            message = "Dzień dobry! Twój rower jest już gotowy do odbioru. Zapraszamy do naszego serwisu w Toruniu przy ulicy Wita Stwosza 2 w tygodniu 10-17 oraz w soboty 10-14."
            sms_notif.publish_text_message(phone_number=lead.lead_contact.phone, message=message)
            lead.sms_sent=True
        except:
            error = {'message': 'Coś nie poszło z wysyłaniem tego typu smsa :<', 'status': 500}
            response  = jsonify(error)
            response.status_code = error['status']
            return response
    else: 
        na = {'message': 'Zlecenie nie jest w statusie "Gotowy" lub sms już został wysłany.', 'status': 406}
        response  = jsonify(na)
        response.status_code = na['status']
        return response
    ok = {'message': 'Wysłano SMS do klienta.', 'status': 200}
    response  = jsonify(ok)
    response.status_code = ok['status']
    db.session.add(lead)
    db.session.commit()
    return response

@login_required
@check_access('leads', 'update')
@leads.route('/leads/update_stage/<int:lead_id>/<int:lead_stage_id>', methods=['GET','POST'])
def update_stage(lead_id, lead_stage_id, owner=None, lead=None) -> Response:
    if not lead:
        lead = LeadMain.query.filter(LeadMain.id == lead_id).first()
    if not owner:
        owner = User.get_current_user()
        lead.owner = owner
    lead_stage = LeadStatus.get_by_id(lead_stage_id)
    # to disable dragging back and forth from final stage
    if lead_stage.is_final == False and lead.status.is_final == True:
        error = {'message': 'Nie można zaktualizować statusu zlecenia w tę strone!', 'status': 500}
        response  = jsonify(error)
        response.status_code = error['status']
        return response
    lead.lead_status_id = lead_stage_id
    send_sms(lead_id=lead.id)
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
@leads.route('/leads/new/_search_for_contact', methods=['GET'])
def search_for_contact():
    # Get the input from the query string
    input = str(request.args.get("name"))
    if len(input) > 2:
        # Query the database for the matching records
        results = Contact.query.filter(Contact.first_name.like(f'%{input}%')).all()
        # Return the phone numbers as a JSON array
        return jsonify([result.first_name for result in results])
    else:
        return {}

@login_required
@check_access('leads', 'view')
@leads.route('/leads/new/_get_contact_phone', methods=['GET'])
def get_contact_phone():
    # Get the input from the query string
    input = request.args.get("name")
    # Query the database for the matching records
    result = Contact.query.filter_by(first_name=input).first()
    # Return the phone numbers as a JSON array
    if result:
        return jsonify(result.phone)
    else:
        return jsonify('No contact found with that name')

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
    json_services = []
    scheduled_services = LeadMain.query.filter(LeadMain.lead_status_id == 2).all()
    for scheduled_service in scheduled_services:
        json_services.append({
            'id' : scheduled_service.id,
            'title' : scheduled_service.title,
            'start' : scheduled_service.date_scheduled.strftime('%Y-%m-%d'),
            'color': 'blue'
        }
            )
    current_services = LeadMain.query.filter(LeadMain.lead_status_id == 1).all()
    for current_service in current_services:
        json_services.append({
            'id' : current_service.id,
            'title' : current_service.title,
            'start' : current_service.date_created.strftime('%Y-%m-%d'),
            'color': 'orange'
        }
            )
    ready_services = LeadMain.query.filter(LeadMain.lead_status_id == 5).all()
    for ready_service in ready_services:
        json_services.append({
            'id' : ready_service.id,
            'title' : ready_service.title,
            'start' : ready_service.date_created.strftime('%Y-%m-%d'),
            'color': 'green'
        }
            )
    return json_services

@leads.route("/leads/new", methods=['GET', 'POST'])
@login_required
@check_access('leads', 'create')
def new_lead():
    found_bike = False
    form = NewLead()
    lead_services = []
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            form.phone.data = form.phone.data.replace("-","").replace(" ", "")
            client = Contact.query.filter_by(phone=form.phone.data).first()
            if not client:
                client = new_contact(first_name=form.first_name.data, phone=form.phone.data, current_user=current_user.id)
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
            if (form.service_name.raw_data is not None) and (form.service_price.raw_data is not None):
                for name, price in zip(form.service_name.raw_data, form.service_price.raw_data):
                    new_service = ServicesToLeads(name=name, price=price)
                    lead.services.append(new_service)
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
            sms_sending = request.form.get('sms_sending')
            if sms_sending == 'on':
                lead.sms_sending = True
            else:
                lead.sms_sending = False
            db.session.add(lead)
            db.session.commit()
            flash('Nowe zlecenie serwisowe utworzone!', 'success')
            return redirect(url_for('leads.get_leads_view'))
        else:
            flash('Błednie wypełniony formularz. Sprawdz go ponownie baranie!', 'danger')
            if (form.service_name.raw_data is not None) and (form.service_price.raw_data is not None):
                i = 0
                for name, price in zip(form.service_name.raw_data, form.service_price.raw_data):
                    lead_services.append({"id": i, "service_name": name, "service_price": price})
                    i+=1
    return render_template("leads/new_lead.html", title="Nowe zlecenie", form=form, services=lead_services)


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
            #contact.last_name = form.last_name.data
            contact.phone = form.phone.data.replace("-","").replace(" ", "")
            bike.manufacturer = form.bike_manufacturer.data
            bike.model = form.bike_model.data
            lead.owner = form.assignees.data
            lead.status = form.lead_status.data
            lead.date_scheduled = form.date_scheduled.data
            lead.notes = form.notes.data
            sms_sending = request.form.get('sms_sending')
            if sms_sending == 'on':
                lead.sms_sending = True
            else:
                lead.sms_sending = False
            lead.services = []
            if (form.service_name.raw_data is not None) and (form.service_price.raw_data is not None):
                for name, price in zip(form.service_name.raw_data, form.service_price.raw_data):
                    service_obj = ServicesToLeads(name=name, price=price)
                    lead.services.append(service_obj)
            up_stage = update_stage(lead_id=lead.id, lead_stage_id=lead.status.id, owner=form.assignees.data, lead=lead)
            if (up_stage.json is not None) and (up_stage.json["status"] == 200):
                db.session.add(lead)
                db.session.commit()
                flash('Zlecenie uaktualnione poprawnie!', 'success')
                clean_up_not_attached_services()
                return redirect(url_for('leads.get_lead_view', lead_id=lead.id))
            else:
                flash('Aktualizacja zlecenia nie powiodła się!', 'danger')
        else:
            print(form.errors)
            flash('Aktualizacja zlecenia nie powiodła się! Sprawdź formularz.', 'danger')
    elif request.method == 'GET':
        form.title.data = lead.title
        form.first_name.data = contact.first_name
        form.phone.data = contact.phone
        form.bike_manufacturer.data = bike.manufacturer
        form.bike_model.data = bike.model
        form.assignees.data = lead.owner
        form.lead_status.data = lead.status
        form.date_scheduled.data = lead.date_scheduled
        form.notes.data = lead.notes
        form.sms_sent.data = lead.sms_sent
        form.sms_sending.data = lead.sms_sending
        form.submit.label = Label('update_lead', 'Aktualizuj')
    return render_template("leads/new_lead.html", title="Aktualizuj zlecenie", form=form, lead_id=lead.id)


@leads.route("/leads/<int:lead_id>")
@login_required
@check_access('leads', 'view')
def get_lead_view(lead_id):
    lead = LeadMain.query.filter_by(id=lead_id).first()
    lead.date_scheduled= lead.date_scheduled.strftime("%Y-%m-%d")
    bike = Bike.get_bike(lead.bike_id)
    contact = Contact.get_contact(lead.contact_id)
    lead.total_price = LeadMain.get_total_price(lead.id)
    return render_template("leads/lead_view.html", title="Przegląd zlecenia", lead=lead, bike=bike, contact=contact)


@leads.route("/leads/del/<int:lead_id>", methods=['GET', 'POST'])
@login_required
@check_access('leads', 'remove')
def delete_lead(lead_id):
    lead = LeadMain.query.filter_by(id=lead_id).first()
    if not lead:
        flash('Zlecenie nie istnieje :(', 'danger')
    else:
        lead = LeadMain.query.filter_by(id=lead_id).first()
        for service in lead.services:
            lead.services.remove(service)
        db.session.commit()
        LeadMain.query.filter_by(id=lead_id).delete()
        db.session.commit()
        flash('Zlecenie usunięte poprawnie', 'success')
    return jsonify({'message': 'Zlecenie usunięte poprawnie', 'status': 200})



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

@leads.before_request
def before_request():
    """Run cleanup before each request"""
    clean_up_not_attached_services()