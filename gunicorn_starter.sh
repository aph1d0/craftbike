#!/bin/sh


# Here we will be spinning up multiple threads with multiple worker processess(-w) and perform a binding.

gunicorn serwis_crm:"create_app()" -w 4 --threads 4 -b 0.0.0.0:80 --timeout 1000