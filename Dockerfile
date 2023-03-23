FROM python:3.10
ENV PYTHONUNBUFFERED 1
RUN MKDIR /app
WORKDIR /app
COPY . /app/
RUN pip3 install --no-cache-dir -r requirements.txt