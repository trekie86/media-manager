FROM python:3 as base
COPY requirements.txt /usr/src/app/requirements.txt
WORKDIR /usr/src/app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
# USER 1000
COPY . /usr/src/app

RUN useradd -ms /bin/bash media-manager-daemon
### Debug Image ###
FROM base as debug
#RUN pip install ptvsd

WORKDIR /usr/src/app/
#CMD python -m ptvsd --host 0.0.0.0 --port 5678 --wait --multiprocess -m uvicorn main:app --host 0.0.0.0 --port 8080
CMD python -m uvicorn main:app --host 0.0.0.0 --port 8080

### Producton Image ###
FROM base as prod

ENTRYPOINT /usr/local/bin/gunicorn \
 -b 0.0.0.0:8080 \
 -w 4 \
 -k uvicorn.workers.UvicornWorker main:app \
 --chdir /usr/src/app

 USER media-manager-daemon
