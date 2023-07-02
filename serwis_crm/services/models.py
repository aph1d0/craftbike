from serwis_crm import db
from sqlalchemy.orm import relationship   

lead_service = db.Table('lead_service',
                    db.Column('lead_id', db.Integer, db.ForeignKey('lead_main.id', ondelete='SET NULL')),
                    db.Column('service_id', db.Integer, db.ForeignKey('services_action.id', ondelete='SET NULL'))
                    )    

class ServicesCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('services_category.id', ondelete='CASCADE'))
    children = db.relationship('ServicesCategory', cascade='all, delete', backref=db.backref('parent', remote_side=[id]))
    service_action = db.relationship('ServicesAction', cascade='all, delete', backref='service_category')

    def __repr__(self):
        return f'<Services Category {self.name}>'
    
    @staticmethod
    def get_by_id(category_id):
        return ServicesCategory.query.filter_by(id=category_id).first()

class ServicesAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('services_category.id', ondelete='CASCADE'))
    
    @staticmethod
    def get_by_id(action_id):
        return ServicesAction.query.filter_by(id=action_id).first()
    
    def __repr__(self):
        return f'<Services Action {self.name}>'
    

