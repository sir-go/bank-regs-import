FROM python:3.10-alpine3.16
WORKDIR /srv

COPY requirements.txt .
RUN pip install --upgrade --no-cache-dir pip &&  \
    pip install --upgrade --no-cache-dir -r requirements.txt

COPY ./app ./app

EXPOSE 8081/tcp

ENTRYPOINT ["gunicorn", "-w 4", "-b", "0.0.0.0:8081", "app:prod()"]
