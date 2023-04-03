import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.html5 import DateField
from wtforms import StringField, SubmitField, FloatField, BooleanField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, Email, Optional, ValidationError, Length
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from serwis_crm.leads.models import LeadStatus
from serwis_crm.users.models import User
from serwis_crm.contacts.models import Contact
from serwis_crm.bikes.models import Bike

class NewService(FlaskForm):
    service_name = StringField('Czynność serwisowa', validators=[DataRequired('Nazwa jest obowiazkowa')])
    service_price = FloatField('Cena czynnośći serwisowej', validators=[DataRequired('Cena jest obowiazkowa')]) 
    submit = SubmitField('Utwórz nowe zlecenie serwisowe')

class NewCategory(FlaskForm):
    category_name = StringField('Czynność serwisowa', validators=[DataRequired('Nazwa jest obowiazkowa')])
    submit = SubmitField('Utwórz nową kategorię serwisową')

class FilterServices(FlaskForm):
    txt_search = StringField()
    submit = SubmitField('Filtruj zlecenia')


class ImportServices(FlaskForm):
    csv_file = FileField('CSV File', validators=[FileAllowed(['csv'])])
    submit = SubmitField('Create Leads')


class BulkDelete(FlaskForm):
    submit = SubmitField('Usuń zaznaczone zlecenia')



