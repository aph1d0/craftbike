FROM python:3.10-slim as build

# Copy the entire directory to the temporary build stage
COPY . /serwis_crm_app

# Remove the .git folder from the build directory
RUN rm -rf /serwis_crm_app/.git

FROM python:3.10-slim
ENV PYTHONUNBUFFERED 1
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}

# RUN apk update && apk add --no-cache python3-dev py3-pip gcc musl-dev mariadb-connector-c-dev

RUN apt-get update && apt-get install -y default-libmysqlclient-dev

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY --from=build /serwis_crm_app /serwis_crm_app
WORKDIR /serwis_crm_app

RUN cp serwis_crm/config_vars.example serwis_crm/config_vars.py && \
    sed -i 's/<database_host>/${MYSQL_HOST}/g' serwis_crm/config_vars.py && \
    sed -i 's/<database_user>/${MYSQL_USER}/g' serwis_crm/config_vars.py && \
    sed -i 's/<database_password>/${MYSQL_PASSWORD}/g' serwis_crm/config_vars.py && \
    sed -i 's/<database_name>/${MYSQL_DB_NAME}/g' serwis_crm/config_vars.py 



ENTRYPOINT ["./gunicorn_starter.sh"]