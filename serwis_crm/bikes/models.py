from datetime import datetime
from serwis_crm import db

class Bike(db.Model):
    __tablename__ = "bikes"
    id = db.Column(db.Integer, db.Sequence('bike_id_seq'), primary_key=True)
    manufacturer = db.Column(db.String(50))
    model = db.Column(db.String(100))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    contact = db.relationship('Contact', backref='contact_bikes', lazy=True)
    lead = db.relationship('LeadMain', backref='bike', lazy=True)

    @staticmethod
    def get_bike(bike_id):
        return Bike.query.filter_by(id=bike_id).first()
        
    @staticmethod
    def get_label(bike):
        return bike.manufacturer + ' ' + bike.model
    
    @staticmethod
    def bike_list_query():
        return Bike.query

    def __repr__(self):
        return f"Bike('{self.manufacturer}', '{self.model}', '{self.contact_id}')"
