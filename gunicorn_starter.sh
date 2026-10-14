#!/bin/sh

set -e

# Przygotowanie bazy (oczekiwanie na baze + migracje alembica).
# Blad na tym etapie przerywa start - kontener nie podniesie sie
# z niezgodnym schematem bazy.
python3 db_bootstrap.py

# Here we will be spinning up multiple threads with multiple worker processess(-w) and perform a binding.

exec opentelemetry-instrument gunicorn serwis_crm:"create_app()" -w 4 --threads 4 -b 0.0.0.0:8003 --timeout 1000 --env "SCRIPT_NAME=/serwis" --access-logfile -
