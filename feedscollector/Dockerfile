FROM python:3.12-slim

RUN apt update -y && apt upgrade -y
RUN apt install build-essential -y

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY feedscollector/requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY feedscollector /code

RUN mkdir -p /code/libs/
COPY libs /code/libs

CMD ["hypercorn", "asgi:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
