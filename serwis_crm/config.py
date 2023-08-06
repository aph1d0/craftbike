import os

class Config(object):
    DEBUG = False
    TESTING = False
    RBAC_USE_WHITE = True
    PYTHON_VER_MIN_REQUIRED = '3.5.0'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.getenv("DEV_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = f'mysql://{os.getenv("DEV_MYSQL_USER")}:{os.getenv("DEV_MYSQL_PASS")}@{os.getenv("DEV_MYSQL_HOST")}/{os.getenv("DEV_MYSQL_DB_NAME")}'


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = os.getenv("TEST_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = f'mysql://{os.getenv("TEST_MYSQL_USER")}:{os.getenv("TEST_MYSQL_PASS")}@{os.getenv("TEST_MYSQL_HOST")}/{os.getenv("TEST_MYSQL_DB_NAME")}'


class ProductionConfig(Config):
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = f'mysql://{os.getenv("MYSQL_USER")}:{os.getenv("MYSQL_PASS")}@{os.getenv("MYSQL_HOST")}/{os.getenv("MYSQL_DB_NAME")}'





