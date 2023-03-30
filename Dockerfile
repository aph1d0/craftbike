FROM python:3.10
ENV PYTHONUNBUFFERED 1
COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY --exclude=.git . /serwis_crm
WORKDIR /serwis_crm

RUN cp config_vars.example config_vars.py && \
    sed -i 's/<database_host>/${MYSQL_HOST}/g' config_vars.py && \
    sed -i 's/<database_user>/${MYSQL_USER}/g' config_vars.py && \
    sed -i 's/<database_password>/${MYSQL_PASSWORD}/g' config_vars.py && \
    sed -i 's/<database_name>/${MYSQL_DB_NAME}/g' config_vars.py 

ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}

ENTRYPOINT ["./gunicorn_starter.sh"]