![Main Foodgram workflow](https://github.com/doonyasonya/foodgram/actions/workflows/main.yml/badge.svg)

# Foodgram

Foodgram - учебный проект, на котором можно выставлять свои рецепты, а также подписываться на рецепты других авторов и самих авторов.

## Стэк проекта

- Python
- Django
- DjangoRestFramework
- PostgreSql
- Gunicorn
- Nginx 

## Ссылка на проект

http://130.193.34.93/

## Запуск проекта

1. Для запуска проекта нужно подключиться к удаленному серверу:
```
ssh -i путь_до_файла_с_SSH_ключом/название_файла_закрытого_SSH-ключа login@ip
```

2. Установка Docker Compose на сервер:
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin
```

3. Создать .env

В каталоге проекта будет лежать env_template, на основе этого файла вам нужно будет создать .env со своими параметрами


4. Запускаем Docker:
```
cd infra
sudo docker compose up
```

## Прод версия и отличия от обычной:
docker-compose - разворачивает проект используя локальные файлы
docker-compose.production - разворачивает проект из образов докерхаба

## Автор проекта - Никитин Данила