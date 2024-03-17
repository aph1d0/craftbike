FROM python:3.10-slim as build

# Copy the entire directory to the temporary build stage
COPY . /serwis_crm_app

# Remove the .git folder from the build directory
RUN rm -rf /serwis_crm_app/.git

FROM python:3.10.12-slim

ARG MYSQL_HOST
ARG MYSQL_PORT
ARG MYSQL_USER
ARG MYSQL_PASSWORD
ARG MYSQL_DB_NAME

ENV PYTHONUNBUFFERED 1

# RUN apk update && apk add --no-cache python3-dev py3-pip gcc musl-dev mariadb-connector-c-dev

RUN apt-get update && apt-get install -y default-libmysqlclient-dev gcc pkg-config 

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY --from=build /serwis_crm_app /serwis_crm_app
WORKDIR /serwis_crm_app

RUN chmod +x ./gunicorn_starter.sh

EXPOSE 8003

ENTRYPOINT ["./gunicorn_starter.sh"]