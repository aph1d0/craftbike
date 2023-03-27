from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.fields.html5 import DateTimeLocalField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, Optional
from wtforms_sqlalchemy.fields import QuerySelectField

from serwis_crm.users.models import User
from serwis_crm.contacts.models import Contact
from serwis_crm.bikes.models import Bike

def filter_bikes_adv_filters_query():
    return [
        {'id': 1, 'title': 'Created Today'},
        {'id': 2, 'title': 'Created Yesterday'},
        {'id': 3, 'title': 'Created In Last 7 Days'},
        {'id': 4, 'title': 'Created In Last 30 Days'}
    ]

class NewBike(FlaskForm):
    bike_manufacturer = StringField('Marka roweru', validators=[DataRequired('Marka roweru jest obowiazkowa')])
    bike_model = StringField('Model roweru', validators=[DataRequired('Model roweru jest obowiazkowy')])
    submit = SubmitField('Create New Deal')


class FilterBikes(FlaskForm):
    txt_search = StringField()

    contacts = QuerySelectField(query_factory=Contact.contact_list_query, get_pk=lambda a: a.id,
                                get_label=Contact.get_label, blank_text='[-- Wybierz klienta --]', allow_blank=True)
    manufacturer = QuerySelectField(query_factory=Bike.bike_list_query, get_pk=lambda a: a.id,
                                get_label=Bike.get_label, blank_text='[-- Wybierz producenta --]', allow_blank=True)
    model = QuerySelectField(query_factory=Bike.bike_list_query, get_pk=lambda a: a.id,
                                get_label=Bike.get_label, blank_text='[-- Wybierz model --]', allow_blank=True)

    submit = SubmitField('Filtruj rowery')
