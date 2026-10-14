"""Przygotowanie bazy danych przed startem aplikacji.

Uruchamiane z gunicorn_starter.sh zanim wystartuje gunicorn, dzieki czemu
schemat bazy jest zawsze zgodny z wdrazanym kodem.

Logika:
  * czeka az baza bedzie osiagalna (deploy moze wyprzedzic start bazy),
  * swieza/pusta baza -> `stamp head`; schemat tworzy db.create_all(),
    a dane poczatkowe (role, statusy zlecen) zaklada instalator aplikacji,
  * istniejaca baza -> `upgrade`, czyli normalne migracje alembica.

Uwaga: migracje w tym repo nie odtwarzaja calego schematu (bazowa rewizja
tworzy tylko tabele test_user) - schemat powstaje przez db.create_all().
Dlatego na pustej bazie robimy `stamp`, a nie `upgrade`: ten drugi
wywrocilby sie na probie zalozenia tabel, ktore create_all juz utworzyl.

Skrypt konczy sie kodem != 0 jesli migracja sie nie powiedzie - kontener
nie wystartuje z niezgodnym schematem, a deploy zglosi blad.
"""
import os
import sys
import time
import traceback

import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy.engine import URL

# tabela, po ktorej poznajemy ze schemat aplikacji juz istnieje
SCHEMA_MARKER_TABLE = 'lead_status'


def log(message, stream=sys.stdout):
    """Wypisuje komunikat bezposrednio na strumien.

    Swiadomie nie uzywamy modulu logging - migrations/env.py wola
    fileConfig(), ktore domyslnie wylacza wczesniej utworzone loggery
    i komunikaty o bledach przepadaja.
    """
    print(f'[db_bootstrap] {message}', file=stream, flush=True)


def build_db_url():
    prefix = {
        'development': 'DEV_',
        'testing': 'TEST_',
    }.get(os.getenv('FLASK_ENV'), '')
    return URL.create(
        'mysql',
        username=os.getenv(f'{prefix}MYSQL_USER'),
        password=os.getenv(f'{prefix}MYSQL_PASSWORD'),
        host=os.getenv(f'{prefix}MYSQL_HOST'),
        port=int(os.getenv(f'{prefix}MYSQL_PORT') or 3306),
        database=os.getenv(f'{prefix}MYSQL_DB_NAME'),
    )


def wait_for_db(url, retries, delay):
    """Zwraca engine do osiagalnej bazy albo przerywa po wyczerpaniu prob."""
    engine = sqlalchemy.create_engine(url, pool_pre_ping=True)
    for attempt in range(1, retries + 1):
        try:
            with engine.connect():
                log(f'Polaczenie z baza nawiazane (proba {attempt}).')
                return engine
        except Exception as exc:
            if attempt == retries:
                log(f'Baza nieosiagalna po {retries} probach: {exc}', sys.stderr)
                engine.dispose()
                raise
            log(f'Baza jeszcze nieosiagalna (proba {attempt}/{retries}), ponawiam za {delay}s.')
            time.sleep(delay)


def main():
    retries = int(os.getenv('DB_WAIT_RETRIES', '30'))
    delay = int(os.getenv('DB_WAIT_DELAY', '2'))

    engine = wait_for_db(build_db_url(), retries, delay)
    try:
        is_fresh_db = not inspect(engine).has_table(SCHEMA_MARKER_TABLE)
    finally:
        engine.dispose()

    # import dopiero teraz - create_app() samo wola db.create_all(),
    # wiec wykrycie pustej bazy musi sie odbyc wczesniej
    from alembic import command
    from flask import current_app

    from serwis_crm import create_app

    app = create_app()
    with app.app_context():
        # alembic wolany bezposrednio, a nie przez flask_migrate.upgrade():
        # tamten opakowuje bledy w sys.exit(1) i gubi ich tresc w logach
        config = current_app.extensions['migrate'].migrate.get_config(None)
        if is_fresh_db:
            log('Pusta baza - oznaczam migracje jako wykonane (stamp head).')
            command.stamp(config, 'head')
        else:
            log('Istniejaca baza - uruchamiam migracje (upgrade head).')
            command.upgrade(config, 'head')
    log('Baza gotowa.')


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc()
        log('Przygotowanie bazy nie powiodlo sie - przerywam start aplikacji.', sys.stderr)
        sys.exit(1)
