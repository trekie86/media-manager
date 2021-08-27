FROM python:3
COPY requirements.txt /usr/src/app/requirements.txt
WORKDIR /usr/src/app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
USER 1000
COPY . /usr/src/app

ENV ACCESS_LOG=${ACCESS_LOG:-/proc/1/fd/1}
ENV ERROR_LOG=${ERROR_LOG:-/proc/1/fd/2}

ENTRYPOINT /usr/local/bin/gunicorn \
 -b 0.0.0.0:8080 \
 -w 4 \
 -k uvicorn.workers.UvicornWorker main:app \
 --chdir /usr/src/app \
 --access-logfile "$ACCESS_LOG" \
 --error-logfile "$ERROR_LOG"