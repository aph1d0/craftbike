from .config_vars import *


class Config(object):
    DEBUG = False
    TESTING = False
    RBAC_USE_WHITE = True
    PYTHON_VER_MIN_REQUIRED = '3.5.0'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = DEV_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = f'mysql://{DEV_DB_USER}:{DEV_DB_PASS}@{DEV_DB_HOST}/{DEV_DB_NAME}'


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = TEST_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = f'mysql://{TEST_DB_USER}:{TEST_DB_PASS}@{TEST_DB_HOST}/{TEST_DB_NAME}'


class ProductionConfig(Config):
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = f'mysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'





