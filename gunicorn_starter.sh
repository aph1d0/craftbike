#!/bin/sh


# Here we will be spinning up multiple threads with multiple worker processess(-w) and perform a binding.

opentelemetry-instrument --logs_exporter otlp gunicorn serwis_crm:"create_app()" -w 4 --threads 4 -b 0.0.0.0:8003 --timeout 1000 --env "SCRIPT_NAME=/serwis" --access-logfile -