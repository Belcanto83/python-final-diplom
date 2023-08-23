FROM python:3.10

ENV HOME=/usr/src/app

RUN mkdir -p $HOME
RUN mkdir -p $HOME/static
WORKDIR $HOME

#RUN apk add --no-cache gcc musl-dev linux-headers

COPY . .

RUN pip --no-cache-dir install -r requirements.txt

#CMD python manage.py migrate (docker-compose exec stocks_products python manage.py migrate)