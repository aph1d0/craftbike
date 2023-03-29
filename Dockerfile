FROM python:3.10
ENV PYTHONUNBUFFERED 1
COPY requirements.txt /
RUN pip3 install -r /requirements.txt


COPY . /serwis_crm
WORKDIR /serwis_crm



ENTRYPOINT ["./gunicorn_starter.sh"]