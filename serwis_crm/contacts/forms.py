from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, Email
from wtforms_sqlalchemy.fields import QuerySelectField

from serwis_crm.users.models import User


class NewContact(FlaskForm):
    first_name = StringField('Imię')
    #last_name = StringField('Nazwisko')
    phone = StringField('Telefon')
    notes = StringField('Notatki', widget=TextArea())
    assignees = QuerySelectField('Przypisz do', query_factory=User.user_list_query, get_pk=lambda a: a.id,
                                 get_label=User.get_label, default=User.get_current_user)
    submit = SubmitField('Stwórz klienta')


def filter_contacts_adv_filters_query():
    return [
        {'id': 1, 'title': 'Stworzone dzisiaj'},
        {'id': 2, 'title': 'Stworzone wczoraj'},
        {'id': 3, 'title': 'Stworzone w ostatnich 7 dniach'},
        {'id': 4, 'title': 'Stworzone w ostatnich 30 dniach'}
    ]


class FilterContacts(FlaskForm):
    txt_search = StringField()
    assignees = QuerySelectField(query_factory=User.user_list_query, get_pk=lambda a: a.id,
                                 get_label=User.get_label, allow_blank=True, blank_text='[-- Wybierz serwisanta --]')
    advanced_user = QuerySelectField(query_factory=filter_contacts_adv_filters_query,
                                     get_pk=lambda a: a['id'],
                                     get_label=lambda a: a['title'],
                                     allow_blank=True, blank_text='[-- filtr zaawansowany --]')

    submit = SubmitField('Filtruj klientów')
