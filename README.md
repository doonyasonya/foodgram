
# Инструкция по запуску проекта с Docker Compose

## Оглавление

1. [Установите необходимые инструменты](#1-установите-необходимые-инструменты)  
2. [Клонируйте репозиторий](#2-клонируйте-репозиторий)  

3. [Создать .env](#3-создать-env)

4. [Перейдите в папку infra](#4-перейдите-в-папку-infra)  

5. [Запустите проект с помощью Docker Compose](#5-запустите-проект-с-помощью-docker-compose)  
6. [Проверьте статус контейнеров](#6-проверьте-статус-контейнеров-опционально)  
7. [Доступ к приложению](#7-доступ-к-приложению)  
8. [Создание суперпользователя Django](#8-создание-суперпользователя-django)  
9. [Остановка контейнеров](#9-остановка-контейнеров-опционально)  
10. [Устранение возможных ошибок](#10-устранение-возможных-ошибок)  

## 1. Установите необходимые инструменты

Перед началом убедитесь, что на вашем компьютере установлены следующие компоненты:

- **Git**: для клонирования репозитория. [Скачать и установить Git](https://git-scm.com/downloads)
- **Docker** и **Docker Compose**: для контейнеризации. [Установка Docker](https://docs.docker.com/get-docker/)

Проверьте их версии, выполнив команды:

```bash
git --version
docker --version
docker compose version  # Для новых версий Docker, иначе используйте `docker-compose --version`
```

---

## 2. Клонируйте репозиторий

Перейдите в директорию, где хотите разместить проект, и выполните команду:

```bash
git clone git@github.com:doonyasonya/foodgram.git
```

Пример:

После клонирования перейдите в папку проекта:

```bash
cd foodgram
```

---

## 3. Создать **.env**

В каталоге проекта будет лежать **.template.env**, на основе этого файла вам нужно будет создать **.env** со своими параметрами (Можно просто переименовать **.template.env** в **.env**)

---

## 4. Перейдите в папку **infra**

Переход в папку **infra**:

```bash
cd infra
```

---

## 5. Запустите проект с помощью Docker Compose

Находясь в папке **infra**, выполните следующую команду:

```bash
docker compose up
```

Эта команда выполнит следующие действия:

- Создаст и запустит необходимые контейнеры (например, контейнеры с базой данных, бэкендом и фронтендом).
- Автоматически загрузит все необходимые данные в базу данных, включая информацию об ингредиентах.

Если вы хотите запустить контейнеры в фоновом режиме (detached mode), используйте флаг `-d`:

```bash
docker compose up -d
```

---

## 6. Проверьте статус контейнеров (опционально)

Чтобы убедиться, что все контейнеры работают корректно, выполните команду:

```bash
docker ps
```

Эта команда покажет список всех запущенных контейнеров.

---

## 7. Доступ к приложению

После успешного запуска контейнеров приложение будет доступно по адресу:

[http://localhost/recipes](http://localhost/recipes)

Откройте этот URL в браузере и проверьте работу приложения.

---

## 8. Создание суперпользователя Django

Для создания суперпользователя, который сможет управлять приложением через административную панель Django, выполните следующую команду:

1. Откройте терминал внутри контейнера с Django:

   ```bash
   docker compose exec django python manage.py createsuperuser
   ```

2. Следуйте инструкциям в терминале: укажите **имя пользователя**, **email** и **пароль**.

После этого вы сможете войти в админ-панель Django по адресу [http://localhost/admin](http://localhost/admin).

---

## 9. Остановка контейнеров (опционально)

Если вам нужно остановить контейнеры, выполните команду:

```bash
docker compose down
```

Эта команда завершит работу всех контейнеров и освободит ресурсы.

---

## 10. Устранение возможных ошибок

- **Ошибка порта**: если порт уже занят, измените порт в файле `docker-compose.yml`.
- **Проблемы с правами доступа**: если Docker требует прав администратора, добавьте перед командой `sudo` (Linux/Mac):

  ```bash
  sudo docker compose up
  ```

---

## 11. Приложение на удаленном сервере

Приложение доступно по адресу - (http://130.193.34.93/)
