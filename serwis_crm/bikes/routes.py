from flask import Blueprint, session
from flask_login import current_user, login_required
from flask import render_template, flash, url_for, redirect, request
from sqlalchemy import or_
import json
from wtforms import Label

from serwis_crm import db
from .models import Bike
from serwis_crm.common.paginate import Paginate
from serwis_crm.common.filters import CommonFilters
from .forms import NewBike, FilterBikes
from .filters import set_date_filters

from serwis_crm.rbac import check_access

bikes = Blueprint('bikes', __name__)


def reset_bike_filters():
    if 'bikes_search' in session:
        session.pop('bikes_search', None)
    if 'bikes_contacts_owner' in session:
        session.pop('bikes_contacts_owner', None)


@bikes.route("/bikes", methods=['GET', 'POST'])
@login_required
@check_access('bikes', 'view')
def get_bikes_view():
    view_t = request.args.get('view_t', 'list', type=str)
    filters = FilterBikes()

    search = CommonFilters.set_search(filters, 'bikes_search')
    contact = CommonFilters.set_contacts(filters, 'Bike', 'bikes_contacts_owner')
    advanced_filters = set_date_filters(filters, 'Bike', 'bikes_date_created')

    query = Bike.query.filter(or_(
        Bike.title.ilike(f'%{search}%')
    ) if search else True) \
        .filter(contact) \
        .filter(advanced_filters) \
        .order_by(Bike.date_created.desc())

    if view_t == 'kanban':
        return render_template("bikes/kanban_view.html", title="Rowery",
                               deals=query.all(),
                               filters=filters)
    else:
        return render_template("bikes/bike_list.html", title="Rowery",
                               deals=Paginate(query), filters=filters)


@bikes.route("/bikes/<int:bike_id>")
@login_required
@check_access('bikes', 'view')
def get_bike_view(bike_id):
    bike = Bike.query.filter_by(id=bike_id).first()
    print(bike.contact)
    return render_template("bikes/bike_view.html", title="Rowery", bike=bike)


@bikes.route("/bikes/new", methods=['GET', 'POST'])
@login_required
@check_access('bikes', 'create')
def new_bike(bike_manufacturer, bike_model, client_id):
    bike = Bike(manufacturer=bike_manufacturer, model=bike_model, contact_id=client_id)
    db.session.add(bike)
    db.session.commit()
    return bike


@bikes.route("/bikes/edit/<int:bikes_id>", methods=['GET', 'POST'])
@login_required
@check_access('bikes', 'update')
def update_bike(bike_id):
    form = NewBike()

    bike = Bike.get_bike(bike_id)
    if not bike:
        return redirect(url_for('bikes.get_bikes_view'))

    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            bike.manufacturer = form.bike_manufacturer.data
            bike.model = form.bike_model.data
            db.session.commit()
            flash('Rower zaktualizowany poprawnie', 'success')
            return redirect(url_for('bikes.get_bikes_view', bike_id=bike.id))
        else:
            print(form.errors)
            flash('Błąd przy aktualizacji danych roweru', 'danger')
    elif request.method == 'GET':
        form.bike_manufacturer.data = bike.manufacturer
        form.bike_model.data = bike.model
        form.submit.label = Label('update_bike', 'Aktualizuj dane roweru')
    return render_template("bikes/new_bike.html", title="Aktualizuj dane roweru", form=form)

@bikes.route("/bikes/reset_filters")
@login_required
@check_access('bikes', 'view')
def reset_filters():
    reset_bike_filters()
    view_t = request.args.get('view_t', 'list', type=str)
    return redirect(url_for('bikes.get_bikes_view', view_t=view_t))

