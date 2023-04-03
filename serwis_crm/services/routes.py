import pandas as pd
from sqlalchemy import cast, not_, or_
from wtforms import Label

from flask import Blueprint, jsonify, session, Response
from flask_login import current_user, login_required
from flask import render_template, flash, url_for, redirect, request

from serwis_crm import config, db
from .models import ServicesAction, ServicesCategory
from serwis_crm.common.paginate import Paginate
from serwis_crm.common.filters import CommonFilters
from .forms import FilterServices, ImportServices, BulkDelete, NewService

from serwis_crm.rbac import check_access, is_admin

services = Blueprint('services', __name__)

@services.route("/services", methods=['GET'])
@login_required
@check_access('services', 'view')
def get_services_categories_view():

    service_cats = ServicesCategory.query.filter(ServicesCategory.parent_id.is_(None)).all()

    return render_template("services/services_list.html", title="Edycja czynności serwisowych",
                           service_categories=service_cats)


@services.route("/services/get_main_categories", methods=['GET'])
@login_required
@check_access('services', 'view')
def get_main_categories():
    service_cats_list = []
    service_cats = ServicesCategory.query.filter(ServicesCategory.parent_id.is_(None)).all()
    for service_cat in service_cats:
        service_cats_list.append({
            "id": service_cat.id,
            "name": service_cat.name,
            })
    return jsonify(service_cats_list)

@services.route("/services/get_subcategories/<int:category_id>", methods=['GET'])
@login_required
@check_access('services', 'view')
def get_subcategories(category_id):
    service_cats_list = []
    service_cats = ServicesCategory.query.filter(ServicesCategory.parent_id==category_id).all()
    for service_cat in service_cats:
        service_cats_list.append({
            "id": service_cat.id,
            "name": service_cat.name,
            })
    return jsonify(service_cats_list)

@services.route("/services/get_action/<int:category_id>", methods=['GET'])
@login_required
@check_access('services', 'view')
def get_actions(category_id):
    service_action = ServicesAction.query.filter(ServicesAction.parent_id==category_id).first()
    if service_action:
        service_action_json = {
                "id": service_action.id,
                "name": service_action.name,
                "price": service_action.price
                }
    else:
        service_action_json = {}
    return jsonify(service_action_json)

@services.route("/services/actions/edit/<int:action_id>/<string:new_tile_name>/<int:new_tile_price>", methods=['POST'])
@login_required
@check_access('services', 'create')
def update_action(action_id,new_tile_name,new_tile_price):
    service_action = ServicesAction.get_by_id(action_id=action_id)
    service_action.name = new_tile_name
    service_action.price = new_tile_price
    db.session.add(service_action)
    db.session.commit()
    return jsonify({"status_code":200, "message": "Czynność serwisowa zaktualizowana."})

@services.route("/services/new", methods=['GET', 'POST'])
@login_required
@check_access('services', 'create')
def new_service():
    form = NewService()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            service = form.service_name.data
            price = form.service_price.data
            fetched_service = ServicesAction.query.filter(ServicesAction.name.ilike(f'%{service}%')).all()
            if not fetched_service:
                new_service = ServicesAction()
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


@services.route("/services/subcategories/del/<int:subcategory_id>", methods=['GET', 'POST'])
@login_required
@check_access('services', 'remove')
def delete_service_subcategory(subcategory_id):
    service_cat = ServicesCategory.get_by_id(subcategory_id)
    if not service_cat:
        return jsonify({"status_code":404, "message": "Nie ma takiej podkategorii!"})
    else:
        ServicesCategory.query.filter(ServicesCategory.id==subcategory_id).delete()
        #delete_subcategories_cascade(service_cat)
        db.session.commit()
    return jsonify({"status_code":200, "message": "Poprawnie usunięto podkategorie i jej wszystkie zależnośći"})


@services.route("/services/subcategories/new/<int:category_id>/<string:new_subcategory_name>", methods=['POST'])
@login_required
@check_access('services', 'create')
def add_new_subcategory(category_id, new_subcategory_name):
    service_cat = ServicesCategory()
    service_cat.name = new_subcategory_name
    service_cat.parent_id = category_id
    db.session.add(service_cat)
    db.session.commit()
    return jsonify({"status_code":200, "message": "Poprawnie dodano podkategorię"})

@services.route("/services/categories/new/<string:new_category_name>", methods=['POST'])
@login_required
@check_access('services', 'create')
def add_new_main_ategory(new_category_name):
    service_cat = ServicesCategory()
    service_cat.name = new_category_name
    service_cat.parent_id = None
    db.session.add(service_cat)
    db.session.commit()
    return jsonify({"status_code":200, "message": "Poprawnie dodano podkategorię"})