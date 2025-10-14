FROM python:3.12-slim

RUN apt update -y && apt upgrade -y
RUN apt install build-essential -y
RUN apt install ffmpeg -y

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY render/requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY render /code

RUN mkdir -p /code/libs/
COPY libs /code/libs

CMD ["python3", "main.py"]
