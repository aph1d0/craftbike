from datetime import datetime
from serwis_crm import db
from flask import Blueprint, request
from flask_login import current_user
from serwis_crm.bikes.models import Bike



class Contact(db.Model):
    __tablename__ = "contact"
    id = db.Column(db.Integer, db.Sequence('contact_id_seq'), primary_key=True)
    first_name = db.Column(db.String(20))
    last_name = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    notes = db.Column(db.String(300), nullable=True)
    #bikes = db.relationship(Bike, backref='contact')
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    leads = db.relationship('LeadMain', backref='lead_contact', lazy=True)

    @staticmethod
    def contact_list_query():
        account = request.args.get('acc', None, type=int)
        contacts = Contact.query\
                .filter(Contact.account_id == account if account else True)
        # else:
        #     contacts = Contact.query \
        #         .filter(Contact.account_id == account if account else True) \
        #         .filter(Contact.owner_id == current_user.id)
        return contacts

    @staticmethod
    def get_label(contact):
        return contact.first_name + ' ' + contact.last_name

    @staticmethod
    def get_contact(contact_id):
        return Contact.query.filter_by(id=contact_id).first()

    def get_contact_name(self):
        if self.last_name:
            return self.first_name + ' ' + self.last_name
        else:
            return None

    def __repr__(self):
        return f"Account('{self.last_name}', '{self.email}', '{self.phone}')"
