import pandas as pd
from sqlalchemy import cast, not_, or_
import sqlalchemy
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
                "price": service_action.default_price
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
    service_action.default_price = new_tile_price
    db.session.add(service_action)
    db.session.commit()
    return jsonify({"status_code":200, "message": "Czynność serwisowa zaktualizowana."})

@services.route("/services/actions/del/<int:action_id>", methods=['POST'])
@login_required
@check_access('services', 'remove')
def delete_action(action_id):
    service_action = ServicesAction.get_by_id(action_id)
    if not service_action:
        return jsonify({"status_code":404, "message": "Nie ma takiej akcji!"})
    else:
        ServicesAction.query.filter(ServicesAction.id==action_id).delete()
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            return jsonify({"status_code":501, "message": "Nie można usunąć czynnośći serwisowej ponieważ jest powiązana z istniejącym serwisem"})  
    return jsonify({"status_code":200, "message": "Poprawnie usunięto czynność serwisową"})    

@services.route("/services/actions/add/<int:category_id>/<string:action_name>/<int:action_price>", methods=['POST'])
@login_required
@check_access('services', 'create')
def add_action(category_id, action_name, action_price):
    service_action = ServicesAction.query.filter(ServicesAction.name==action_name).first()
    if service_action:
        return jsonify({"status_code":501, "message": "Taka akcja serwisowa juz istnieje!"})
    else:
        new_service_action = ServicesAction()
        new_service_action.name = action_name
        new_service_action.parent_id = category_id
        new_service_action.default_price = action_price
        db.session.add(new_service_action)
        db.session.commit()
        return jsonify({"status_code":200, "message": "Poprawnie dodano czynność serwisową"})    

@services.route("/services/subcategories/del/<int:subcategory_id>", methods=['GET', 'POST'])
@login_required
@check_access('services', 'remove')
def delete_service_subcategory(subcategory_id):
    service_cat = ServicesCategory.get_by_id(subcategory_id)
    if not service_cat:
        return jsonify({"status_code":404, "message": "Nie ma takiej podkategorii!"})
    else:
        ServicesCategory.query.filter(ServicesCategory.id==subcategory_id).delete()
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