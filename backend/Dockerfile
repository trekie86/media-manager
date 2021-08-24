FROM python:3
COPY requirements.txt /usr/src/app/requirements.txt
WORKDIR /usr/src/app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
USER 1000
COPY . /usr/src/app
CMD ["main.py"]
ENTRYPOINT ["python3"]