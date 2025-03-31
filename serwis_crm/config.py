import os

class Config(object):
    DEBUG = False
    TESTING = False
    RBAC_USE_WHITE = True
    PYTHON_VER_MIN_REQUIRED = '3.5.0'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
        "echo": False,
    }
    SQLALCHEMY_POOL_TIMEOUT = 30


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.getenv("DEV_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = f'mysql://{os.getenv("DEV_MYSQL_USER")}:{os.getenv("DEV_MYSQL_PASSWORD")}@{os.getenv("DEV_MYSQL_HOST")}:{os.getenv("DEV_MYSQL_PORT")}/{os.getenv("DEV_MYSQL_DB_NAME")}'


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = os.getenv("TEST_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = f'mysql://{os.getenv("TEST_MYSQL_USER")}:{os.getenv("TEST_MYSQL_PASSWORD")}@{os.getenv("TEST_MYSQL_HOST")}:{os.getenv("TEST_MYSQL_PORT")}/{os.getenv("TEST_MYSQL_DB_NAME")}'


class ProductionConfig(Config):
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = f'mysql://{os.getenv("MYSQL_USER")}:{os.getenv("MYSQL_PASSWORD")}@{os.getenv("MYSQL_HOST")}:{os.getenv("MYSQL_PORT")}/{os.getenv("MYSQL_DB_NAME")}'
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
    }




