FROM python:3.12.4-alpine as build

# Copy the entire directory to the temporary build stage
COPY . /serwis_crm_app

FROM python:3.12.4-alpine

ARG MYSQL_HOST
ARG MYSQL_PORT
ARG MYSQL_USER
ARG MYSQL_PASSWORD
ARG MYSQL_DB_NAME
ARG GITHUB_SHA

ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev g++ libffi-dev openssl-dev ca-certificates\
    && apk add --no-cache mariadb-dev mariadb-client git bzip2-dev coreutils libc-dev libffi-dev linux-headers

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY --from=build /serwis_crm_app /serwis_crm_app
WORKDIR /serwis_crm_app

ENV NEW_RELIC_APP_NAME="CraftBike serwis"
ENV NEW_RELIC_LOG=stdout
ENV NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true
ENV NEW_RELIC_LOG_LEVEL=info

RUN chmod +x ./gunicorn_starter.sh

EXPOSE 8003

ENTRYPOINT ["./gunicorn_starter.sh"]