# syntax=docker/dockerfile:1 **<-- Bei manchen Systemen muss diese Zeile weg**

# FROM python:3
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

# WORKDIR /usr/src/app
WORKDIR /app


COPY requirements.txt ./

# RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt



COPY . . 

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]