from datetime import datetime
from serwis_crm import db
from sqlalchemy.orm import relationship   

lead_service = db.Table('lead_service',
                    db.Column('lead_id', db.Integer, db.ForeignKey('lead_main.id')),
                    db.Column('service_id', db.Integer, db.ForeignKey('services.id'))
                    )    

class Services(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    price = db.Column(db.Float(2))

    def __repr__(self):
        return f'Service("{self.name}")'    

class LeadStatus(db.Model):
    id = db.Column(db.Integer, db.Sequence('lead_status_id_seq'), primary_key=True)
    status_name = db.Column(db.String(40), unique=True, nullable=False)
    is_final = db.Column(db.Boolean, nullable=False)
    leads = db.relationship('LeadMain', backref='status', lazy=True)

    @staticmethod
    def lead_status_query():
        return LeadStatus.query.order_by(LeadStatus.id.asc())
    
    @staticmethod
    def lead_status_query_final():
        return LeadStatus.query.filter(LeadStatus.is_final==False).order_by(LeadStatus.id.asc())

    @staticmethod
    def get_by_id(lead_status_id):
        return LeadStatus.query.filter_by(id=lead_status_id).first()

    def __repr__(self):
        return f"LeadStatus('{self.status_name}')"



class LeadMain(db.Model):
    id = db.Column(db.Integer, db.Sequence('lead_id_seq'), primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    bike_id = db.Column(db.Integer, db.ForeignKey('bikes.id'), nullable=False)
    notes = db.Column(db.String(200), nullable=True)
    lead_status_id = db.Column(db.Integer, db.ForeignKey('lead_status.id', ondelete='SET NULL'), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_scheduled= db.Column(db.DateTime, nullable=True)
    services = db.relationship('Services', secondary=lead_service, backref='leads')

    @staticmethod
    def get_by_id(lead_id):
        return LeadMain.query.filter_by(id=lead_id).first()
    
    def get_total_price(lead_id):
        total=0
        lead = LeadMain.query.filter_by(id=lead_id).first()
        if lead.services:
            for service in lead.services:
                total += float(service.price)
        return total


    def __repr__(self):
        return f"Lead('{self.last_name}')"

