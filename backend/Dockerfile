FROM python:3.11

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p /app/static /app/media \
    && chmod 755 /app \
    && chmod -R 777 /app/static /app/media

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]