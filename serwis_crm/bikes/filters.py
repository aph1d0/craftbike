from flask import session, request
from flask_login import current_user
from .forms import filter_bikes_adv_filters_query
from datetime import date, timedelta
from sqlalchemy import text

def set_filters(f_id):
    today = date.today()
    filter_d = True
    if f_id == 1:
        filter_d = text('bike.contact_id IS NULL')
    elif f_id == 2:
        filter_d = text('bike.manufacturer IS NULL')
    elif f_id == 3:
        filter_d = text('bike.model IS NULL')

    return filter_d

def assign_filter(filter_obj, key):
    filter_d = True
    if filter_obj.data:
        filter_d = set_filters(filter_obj.data['id'])
        session[key] = filter_obj.data['id']
    else:
        if key in session:
            session.pop(key, None)
    return filter_d
