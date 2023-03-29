import pandas as pd
from sqlalchemy import cast, or_
from wtforms import Label

from flask import Blueprint, session, Response
from flask_login import current_user, login_required
from flask import render_template, flash, url_for, redirect, request

from serwis_crm import config, db
from .models import Services
from serwis_crm.common.paginate import Paginate
from serwis_crm.common.filters import CommonFilters
from .forms import FilterServices, ImportServices, BulkDelete, NewService

from serwis_crm.rbac import check_access, is_admin

services = Blueprint('services', __name__)

def reset_service_filters():
    if 'service_search' in session:
        session.pop('service_search', None)



@services.route("/services", methods=['GET', 'POST'])
@login_required
@check_access('services', 'view')
def get_services_view():
    filters = FilterServices()
    search = CommonFilters.set_search(filters, 'service_search')

    if search:
        query = Services.query \
            .filter(
                Services.name.ilike(f'%{search}')
            )
    else:
        query = Services.query

    bulk_form = {
        'delete': BulkDelete()
    }

    return render_template("services/services_list.html", title="Widok czynności serwisowych",
                           services=Paginate(query), filters=filters, bulk_form=bulk_form)

@services.route("/services/new", methods=['GET', 'POST'])
@login_required
@check_access('services', 'create')
def new_service():
    form = NewService()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            service = form.service_name.data
            price = form.service_price.data
            fetched_service = Services.query.filter(Services.name.ilike(f'%{service}%')).all()
            if not fetched_service:
                new_service = Services()
                new_service.name = service
                new_service.price = price
                db.session.add(new_service)
                db.session.commit()
                flash('Nowa czynność serwisowa została utworzona!', 'success')
            else:
                flash('Czynność o takiej nazwie już istnieje! Zapraszam do użycia przycisku szukaj.', 'danger')
            return redirect(url_for('services.get_services_view'))
        else:
            for error in form.errors:
                print(error)
            flash('Błednie wypełniony formularz. Sprawdz go ponownie baranie!', 'danger')
    return render_template("services/new_service.html", title="Nowa czynność serwisowa", form=form)


@services.route("/services/edit/<int:service_id>", methods=['GET', 'POST'])
@login_required
@check_access('services', 'update')
def update_service(service_id):
    service = Services.get_by_id(service_id)
    if not service:
        return redirect(url_for('services.get_services_view'))

    form = NewService()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            service.name = form.service_name.data
            service.price = form.service_price.data
            db.session.commit()
            flash('Czynność serwisowa uaktualniona poprawnie!', 'success')
            return redirect(url_for('services.get_service_view', service_id=service.id))
        else:
            print(form.errors)
            flash('Aktualizacja czynnośći nie powiodła się! Sprawdź formularz.', 'danger')
    elif request.method == 'GET':
        form.service_name.data = service.name
        form.service_price.data = service.price
        form.submit.label = Label('update_service', 'Aktualizuj czynność serwisową')
    return render_template("services/new_service.html", title="Aktualizuj czynność serwisową", form=form, service_id=service.id)


@services.route("/services/<int:service_id>")
@login_required
@check_access('services', 'view')
def get_service_view(service_id):
    service = Services.query.filter_by(id=service_id).first()
    return render_template("services/service_view.html", title="Przegląd zlecenia", service=service)


@services.route("/services/del/<int:service_id>")
@login_required
@check_access('services', 'remove')
def delete_service(service_id):
    service = Services.get_by_id(service_id)
    if not service:
        flash('Czynność serwisowa nie istnieje :(', 'danger')
    elif service.leads:
        lead_titles = []
        for lead_title in service.leads:
            lead_titles.append(lead_title.title)
        flash(f'Czynność nie może zostać usunięta ponieważ odnosi sie do serwisów: {lead_titles}', 'danger')
    else:
        Services.query.filter_by(id=service_id).delete()
        db.session.commit()
        flash('Czynność serwisowa usunięta poprawnie', 'success')
    return redirect(url_for('services.get_services_view'))



@services.route("/services/import", methods=['GET', 'POST'])
@login_required
@is_admin
def import_bulk_services():
    form = ImportServices()
    if request.method == 'POST':
        ind = 0
        if form.is_submitted() and form.validate():
            data = pd.read_csv(form.csv_file.data)

            for _, row in data.iterrows():
                service = Services(service_name=row['service_name'], service_price=row['service_price'])
                db.session.add(service)
                ind = ind + 1

            db.session.commit()
            flash(f'{ind} nowych czynności serwisowych zostało zaimportowanych!', 'success')
        else:
            flash('Błednie wypełniony formularz. Sprawdz go ponownie baranie!', 'danger')
    return render_template("services/services_import.html", title="Import czynności serwisowych", form=form)


@services.route("/services/reset_filters")
@login_required
@check_access('services', 'view')
def reset_filters():
    reset_service_filters()
    return redirect(url_for('services.get_services_view'))


@services.route("/services/bulk_delete", methods=['POST'])
@is_admin
def bulk_delete():
    form = BulkDelete()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            ids = [int(x) for x in request.form['services_to_delete'].split(',')]
            Services.query \
                .filter(Services.id.in_(ids)) \
                .delete(synchronize_session=False)
            db.session.commit()
            flash(f'Poprawnie usunięto {len(ids)} czynnośći serwisowych!', 'success')
        else:
            print(form.errors)
    return redirect(url_for('services.get_services_view'))


@services.route("/services/write_csv")
@login_required
def write_to_csv():
    ids = [int(x) for x in request.args.get('services_ids').split(',')]
    query = Services.query \
        .filter(Services.id.in_(ids))
    csv = 'service_name, service_price \n'
    for service in query.all():
        csv += f'{service.service_name},{service.service_price}\n'
    return Response(csv,
                    mimetype='text/csv',
                    headers={"Content-disposition":
                             "attachment; filename=services.csv"})
