# Blog API

Django REST Framework проект с JWT-аутентификацией, кастомным пользователем (email),
правами доступа, кэшированием в Redis, отправкой писем через SMTP в фоне (Celery) и
периодическими задачами (Celery Beat).

## Стек

- Django 5 + Django REST Framework
- djangorestframework-simplejwt (JWT)
- PostgreSQL (или SQLite для быстрого теста)
- Redis (кэш + брокер Celery)
- Celery + Celery Beat (django-celery-beat)
- SMTP (email backend)

## Структура проекта

```
blog_api/
├── manage.py
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Blog_API.postman_collection.json
├── blog_api/          # настройки, celery.py, urls.py
├── users/              # кастомный User, регистрация, JWT-эндпоинты
└── posts/              # модель Post, permissions, кэш
```

## 1. Установка

```bash
cd blog_api
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# отредактируйте .env: задайте SECRET_KEY, данные SMTP и т.д.
```

Для самого быстрого старта без Postgres поставьте в `.env`:
```
USE_SQLITE=True
```

## 2. Поднять Postgres и Redis (если не используете SQLite)

```bash
docker compose up -d
```

## 3. Миграции и суперпользователь

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser   # спросит email и пароль (username не нужен)
```

## 4. Запуск сервисов (в отдельных терминалах)

**Django сервер:**
```bash
python manage.py runserver
```

**Celery worker** (обрабатывает отправку писем):
```bash
celery -A blog_api worker -l info
```

**Celery Beat** (запускает периодическую задачу каждые 5 минут):
```bash
celery -A blog_api beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

После запуска Beat каждые 5 минут в консоли worker'а будет появляться:
```
✅ Периодическая задача Celery Beat выполнена успешно
```

> Если нет реального SMTP-сервера под рукой, для проверки Celery-письма можно
> временно переключить в `settings.py`:
> `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` —
> письмо будет печататься в консоли worker'а вместо реальной отправки.

## 5. Тестирование в Postman

Импортируйте файл `Blog_API.postman_collection.json` в Postman
(Import → Upload Files). Коллекция уже содержит переменные
`base_url`, `access_token`, `refresh_token`, `post_id`, которые
автоматически заполняются скриптами тестов после каждого запроса.

Порядок запросов:

| # | Запрос | Метод | Эндпоинт | Требует токен |
|---|--------|-------|----------|----------------|
| 1 | Register | POST | `/api/auth/register/` | нет |
| 2 | Login | POST | `/api/auth/login/` | нет |
| 3 | Refresh Token | POST | `/api/auth/token/refresh/` | нет (нужен refresh) |
| 4 | Me | GET | `/api/auth/me/` | да |
| 5 | List Posts | GET | `/api/posts/` | нет (кэш на 1 мин) |
| 6 | Create Post | POST | `/api/posts/` | да |
| 7 | Retrieve Post | GET | `/api/posts/{id}/` | нет |
| 8 | Update Post | PATCH | `/api/posts/{id}/` | да, только автор |
| 9 | Delete Post | DELETE | `/api/posts/{id}/` | да, только автор |

### Пример: регистрация
```json
POST /api/auth/register/
{
  "email": "author@example.com",
  "password": "StrongPass123",
  "first_name": "Ivan",
  "last_name": "Ivanov"
}
```
После этого запроса в консоли Celery worker появится задача `send_welcome_email`,
и на указанный email придёт приветственное письмо (или оно распечатается в
консоли, если используется `console.EmailBackend`).

### Пример: вход и получение JWT
```json
POST /api/auth/login/
{
  "email": "author@example.com",
  "password": "StrongPass123"
}
```
Ответ:
```json
{
  "refresh": "eyJhbGciOi...",
  "access": "eyJhbGciOi..."
}
```
Используйте `access` токен в заголовке `Authorization: Bearer <access>`
для всех защищённых запросов.

### Проверка прав доступа (permissions)
1. Зарегистрируйте двух пользователей (author@example.com и other@example.com).
2. Создайте пост от имени `author@example.com`.
3. Залогиньтесь как `other@example.com` и попробуйте выполнить PATCH/DELETE
   этого поста — сервер вернёт `403 Forbidden`.
4. GET-запросы (просмотр списка/деталей поста) доступны без авторизации всем.

### Проверка Redis-кэша
1. Выполните `GET /api/posts/` — Django выполнит запрос к БД и положит
   результат в Redis на 60 секунд.
2. Повторите запрос сразу же — ответ придёт из кэша (можно проверить время
   отклика или добавить лог в `views.py`).
3. Создайте/измените/удалите пост — кэш инвалидируется автоматически
   (`cache.delete(...)` в `perform_create/update/destroy`).

## Основные эндпоинты

```
POST   /api/auth/register/       — регистрация
POST   /api/auth/login/          — вход (получение access/refresh)
POST   /api/auth/token/refresh/  — обновление access-токена
GET    /api/auth/me/             — текущий пользователь

GET    /api/posts/               — список постов (кэш 1 мин)
POST   /api/posts/               — создать пост (авторизован)
GET    /api/posts/{id}/          — детали поста
PUT    /api/posts/{id}/          — полное обновление (только автор)
PATCH  /api/posts/{id}/          — частичное обновление (только автор)
DELETE /api/posts/{id}/          —  ько автор)

/admin/                          — Django admin
```
