import os

class Config(object):
    DEBUG = False
    TESTING = False
    RBAC_USE_WHITE = True
    PYTHON_VER_MIN_REQUIRED = '3.5.0'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = DEV_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = f'mysql://{os.environ["DEV_MYSQL_USER"]}:{os.environ["DEV_MYSQL_PASS"]}@{os.environ["DEV_MYSQL_HOST"]}/{os.environ["DEV_MYSQL_DB_NAME"]}'


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = TEST_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = f'mysql://{os.environ["TEST_MYSQL_USER"]}:{os.environ["TEST_MYSQL_PASS"]}@{os.environ["TEST_MYSQL_HOST"]}/{os.environ["TEST_MYSQL_DB_NAME"]}'


class ProductionConfig(Config):
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = f'mysql://{os.environ["MYSQL_USER"]}:{os.environ["MYSQL_PASS"]}@{os.environ["MYSQL_HOST"]}/{os.environ["MYSQL_DB_NAME"]}'





