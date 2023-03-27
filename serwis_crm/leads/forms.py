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
    submit = SubmitField('Utwórz nowe zlecenie serwisowe')


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


# class ConvertLead(FlaskForm):
#     title = StringField('Deal Title', validators=[DataRequired('Deal title is mandatory')])
#     use_account_information = BooleanField('Use Account Information', default=True)
#     account_name = StringField('Account Name')
#     account_email = StringField('Account Email')

#     use_contact_information = BooleanField('Use Contact Information', default=False)
#     contact_first_name = StringField('Contact First Name')
#     contact_last_name = StringField('Contact Last Name')
#     contact_email = StringField('Contact Email',
#                                 validators=[Optional(), Email(message='Invalid email address!')])
#     contact_phone = StringField('Contact Phone')
#     contacts = QuerySelectField('Contact', query_factory=Contact.contact_list_query, get_pk=lambda a: a.id,
#                                 get_label=Contact.get_label, blank_text='Select A Contact', allow_blank=True)

#     create_deal = BooleanField('Create Deal', default=True)

#     expected_close_price = FloatField('Expected Close Price',
#                                       validators=[DataRequired('Expected Close Price is mandatory')])
#     expected_close_date = DateField('Expected Close Date', format='%Y-%m-%d',
#                                     validators=[Optional()])
#     deal_stages = QuerySelectField('Deal Stage', query_factory=DealStage.deal_stage_list_query, get_pk=lambda a: a.id,
#                                    get_label=DealStage.get_label, allow_blank=False,
#                                    validators=[DataRequired(message='Please select deal stage')])

#     assignees = QuerySelectField('Assign To', query_factory=User.user_list_query, get_pk=lambda a: a.id,
#                                  get_label=User.get_label, default=User.get_current_user)
#     submit = SubmitField('Covert Lead')


class BulkOwnerAssign(FlaskForm):
    owners_list = QuerySelectField('Assign Owner', query_factory=User.user_list_query, get_pk=lambda a: a.id,
                                   get_label=User.get_label, default=User.get_current_user, allow_blank=False,
                                   validators=[DataRequired(message='Prosze wybrać serwisanta')])
    submit = SubmitField('Assign Owner')


class BulkLeadStatusAssign(FlaskForm):
    lead_status_list = QuerySelectField(query_factory=LeadStatus.lead_status_query, get_pk=lambda a: a.id,
                                        get_label='status_name', allow_blank=False,
                                        validators=[DataRequired(message='Prosze wybrać status zlecenia')])
    submit = SubmitField('Assign Lead Status')


class BulkDelete(FlaskForm):
    submit = SubmitField('Delete Selected Leads')



