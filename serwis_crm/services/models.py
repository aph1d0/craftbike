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
    
    @staticmethod
    def get_by_id(service_id):
        return Services.query.filter_by(id=service_id).first()
