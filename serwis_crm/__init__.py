import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from sqlalchemy import inspect, text
# from opentelemetry.instrumentation.flask import FlaskInstrumentor
# from opentelemetry.instrumentation.logging import LoggingInstrumentor
import os

from .config import DevelopmentConfig, TestConfig, ProductionConfig

# database handle
db = SQLAlchemy(session_options={"autoflush": False})

# encryptor handle
bcrypt = Bcrypt()

# manage user login
login_manager = LoginManager()

# function name of the login route that
# tells the path which facilitates authentication
login_manager.login_view = 'users.login'

def run_install(app_ctx):
    from serwis_crm.install.routes import install
    app_ctx.register_blueprint(install)
    return app_ctx


def create_app(config_class=ProductionConfig):
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app = Flask(__name__, instance_relative_config=True)
    #FlaskInstrumentor().instrument_app(app)
    # Auto-instrument logging
    # LoggingInstrumentor().instrument(set_logging_format=True)

    if os.getenv('FLASK_ENV') == 'development':
        config_class = DevelopmentConfig()
    elif os.getenv('FLASK_ENV') == 'production':
        config_class = ProductionConfig()
    elif os.getenv('FLASK_ENV') == 'testing':
        config_class = TestConfig()

    app.config.from_object(config_class)
    app.url_map.strict_slashes = False
    app.jinja_env.globals.update(zip=zip)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Add session cleanup after request
    @app.teardown_request
    def shutdown_session(exception=None):
        if hasattr(db, 'session'):
            db.session.remove()
            db.session.close()
        if hasattr(db, 'engine'):
            db.engine.dispose()

    # Add health check endpoint
    @app.route('/health')
    def health_check():
        try:
            db.session.execute(text('SELECT 1'))
            return {'status': 'healthy'}, 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}, 500

    with app.app_context():
        # check if the config table exists, otherwise run install
        db.create_all()
        engine = db.engine
        #engine.echo = True
        #if not engine.dialect.has_table(engine, 'app_config'):
        if not inspect(engine).has_table('app_config'):
            return run_install(app)
        else:
            from serwis_crm.settings.models import AppConfig
            row = AppConfig.query.first()
            if not row:
                return run_install(app)

        # application is installed so extends the config
        from serwis_crm.settings.models import AppConfig, Currency, TimeZone
        app_cfg = AppConfig.query.first()
        app.config['def_currency'] = Currency.get_currency_by_id(app_cfg.default_currency)
        app.config['def_tz'] = TimeZone.get_tz_by_id(app_cfg.default_timezone)

        # include the routes
        # from serwis_crm import routes
        from serwis_crm.main.routes import main
        from serwis_crm.users.routes import users
        from serwis_crm.leads.routes import leads
        from serwis_crm.contacts.routes import contacts
        from serwis_crm.bikes.routes import bikes
        from serwis_crm.settings.routes import settings
        from serwis_crm.settings.app_routes import app_config
        from serwis_crm.services.routes import services

        # register routes with blueprint
        app.register_blueprint(main)
        app.register_blueprint(users)
        app.register_blueprint(settings)
        app.register_blueprint(app_config)
        app.register_blueprint(leads)
        app.register_blueprint(contacts)
        app.register_blueprint(bikes)
        app.register_blueprint(services)
        return app


