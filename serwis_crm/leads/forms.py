import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.html5 import DateField
from wtforms import StringField, SubmitField, FloatField, BooleanField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, Email, Optional, ValidationError, Length
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
import phonenumbers

from serwis_crm.leads.models import LeadStatus
from serwis_crm.users.models import User
from serwis_crm.contacts.models import Contact
from serwis_crm.bikes.models import Bike


def validate_phone(self, phone):
    try:
        p = phonenumbers.parse(phone.data)
        if not phonenumbers.is_valid_number(p):
            raise ValueError()
    except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
        raise ValidationError('Nieprawidłowy numer telefonu')

class NewLead(FlaskForm):
    phone = StringField('Telefon', validators=[DataRequired(message='Numer telefonu jest obowiązkowy!'), validate_phone])
    bike_manufacturer = StringField('Marka roweru', id='bike_manufacturer', validators=[DataRequired(message='Marka roweru jest obowiązkowa!')])
    bike_model = StringField('Model roweru', id='bike_model', validators=[DataRequired(message='Model roweru jest obowiązkowy!')])
    title = StringField('Nazwa', id='title')
    first_name = StringField('Imię', validators=[DataRequired(message='Imię jest obowiązkowe!')])
    last_name = StringField('Nazwisko', validators=[DataRequired(message='Nazwisko jest obowiązkowe!')])
    notes = StringField('Notatki', widget=TextArea())
    lead_status = QuerySelectField('Status', query_factory=LeadStatus.lead_status_query_final, get_pk=lambda a: a.id,
                                   get_label='status_name', default=LeadStatus.get_by_id(2), allow_blank=False, blank_text='Wybierz status zlecenia')

    assignees = QuerySelectField('Przypisz do', query_factory=User.user_list_query, get_pk=lambda a: a.id,
                                 get_label=User.get_label, default=User.get_current_user)
    date_scheduled = StringField('Data wizyty', id='date_scheduled', default=datetime.datetime.now().strftime('%Y-%m-%d'),
                                 validators=[Length(max=10, message='Cos sie data nie zgadza.')])
    service_name = StringField('Czynność serwisowa')
    service_price = FloatField('Cena czynnośći serwisowej') 
    total_price = FloatField('Cena całkowita serwisu') 
    submit = SubmitField('Utwórz nowe zlecenie serwisowe')

class EditLead(NewLead):
        lead_status = QuerySelectField('Status', query_factory=LeadStatus.lead_status_query, get_pk=lambda a: a.id,
                                   get_label='status_name', default=LeadStatus.get_by_id(2), allow_blank=False, blank_text='Wybierz status zlecenia')

def filter_leads_adv_filters_admin_query():
    return [
            {'id': 1, 'title': 'Nieprzypisane'},
            {'id': 2, 'title': 'Stworzone dzisiaj'},
            {'id': 3, 'title': 'Stworzone wczoraj'},
            {'id': 4, 'title': 'Stworzone w ostatnich 7 dniach'},
            {'id': 5, 'title': 'Stworzone w ostatnich 30 dniach'}
    ]


def filter_leads_adv_filters_user_query():
    return [
            {'id': 2, 'title': 'Stworzone dzisiaj'},
            {'id': 3, 'title': 'Stworzone wczoraj'},
            {'id': 4, 'title': 'Stworzone w ostatnich 7 dniach'},
            {'id': 5, 'title': 'Stworzone w ostatnich 30 dniach'}
    ]


class FilterLeads(FlaskForm):
    txt_search = StringField()
    lead_status = QuerySelectMultipleField(query_factory=LeadStatus.lead_status_query, get_pk=lambda a: a.id,
                                    get_label='status_name', allow_blank=False)
    assignees = QuerySelectField(query_factory=User.user_list_query, get_pk=lambda a: a.id,
                                 get_label=User.get_label, allow_blank=True, blank_text='[-- Wybierz serwisanta --]')
    contacts = QuerySelectField(query_factory=Contact.contact_list_query, get_pk=lambda a: a.id,
                                 get_label=Contact.get_label, allow_blank=True, blank_text='[-- Wybierz klienta --]')
    advanced_admin = QuerySelectField(query_factory=filter_leads_adv_filters_admin_query,
                                get_pk=lambda a: a['id'],
                                get_label=lambda a: a['title'],
                                allow_blank=True, blank_text='[-- filtr zaawansowany --]')

    advanced_user = QuerySelectField(query_factory=filter_leads_adv_filters_user_query,
                                get_pk=lambda a: a['id'],
                                get_label=lambda a: a['title'],
                                allow_blank=True, blank_text='[-- filtr zaawansowany --]')

    submit = SubmitField('Filtruj zlecenia')


class ImportLeads(FlaskForm):
    csv_file = FileField('CSV File', validators=[FileAllowed(['csv'])])
    submit = SubmitField('Create Leads')


class BulkOwnerAssign(FlaskForm):
    owners_list = QuerySelectField('Przypisz serwisanta', query_factory=User.user_list_query, get_pk=lambda a: a.id,
                                   get_label=User.get_label, default=User.get_current_user, allow_blank=False,
                                   validators=[DataRequired(message='Prosze wybrać serwisanta')])
    submit = SubmitField('Przypisz serwisanta')


class BulkLeadStatusAssign(FlaskForm):
    lead_status_list = QuerySelectField(query_factory=LeadStatus.lead_status_query, get_pk=lambda a: a.id,
                                        get_label='status_name', allow_blank=False,
                                        validators=[DataRequired(message='Prosze wybrać status zlecenia')])
    submit = SubmitField('Przypisz status')


class BulkDelete(FlaskForm):
    submit = SubmitField('Usuń zaznaczone zlecenia')



