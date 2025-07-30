FROM python:3.12-slim

RUN apt update -y && apt upgrade -y
RUN apt install build-essential -y
RUN apt install ffmpeg -y
RUN apt install yt-dlp -y
RUN apt install rclone -y

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY src/ /code

CMD ["hypercorn", "asgi:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
