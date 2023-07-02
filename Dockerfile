FROM python:3.10-slim as build

# Copy the entire directory to the temporary build stage
COPY . /serwis_crm_app

# Remove the .git folder from the build directory
RUN rm -rf /serwis_crm_app/.git

FROM python:3.12.0b3-slim

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION
ARG MYSQL_HOST
ARG MYSQL_USER
ARG MYSQL_PASSWORD
ARG MYSQL_DB_NAME

ENV PYTHONUNBUFFERED 1
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}

# RUN apk update && apk add --no-cache python3-dev py3-pip gcc musl-dev mariadb-connector-c-dev

RUN apt-get update && apt-get install -y default-libmysqlclient-dev gcc pkg-config 

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY --from=build /serwis_crm_app /serwis_crm_app
WORKDIR /serwis_crm_app

RUN cp serwis_crm/config_vars.example serwis_crm/config_vars.py && \
    sed -i "s/<database_host>/${MYSQL_HOST}/g" serwis_crm/config_vars.py && \
    sed -i "s/<database_user>/${MYSQL_USER}/g" serwis_crm/config_vars.py && \
    sed -i "s/<database_password>/${MYSQL_PASSWORD}/g" serwis_crm/config_vars.py && \
    sed -i "s/<database_name>/${MYSQL_DB_NAME}/g" serwis_crm/config_vars.py 

RUN chmod +x ./gunicorn_starter.sh

ENTRYPOINT ["./gunicorn_starter.sh"]