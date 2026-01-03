# SMOKECODEX

Бэкенд для сайта бронирования комнат/столов в кальянных на FastAPI + PostgreSQL.

## Быстрый старт (Windows/macOS/Linux)

> Требования: установлен Docker Desktop.

```bash
docker compose up --build
```

После запуска в консоли будет лог с адресами:

- API: http://localhost:8000 (Swagger: http://localhost:8000/docs)
- Фронтенд-заглушка: http://localhost:3000

## Скрипты запуска

### Windows

```bat
start.bat
```

### macOS/Linux

```bash
./start.sh
```

## Архитектура

### Контейнеры

- **db**: PostgreSQL 16
- **backend**: FastAPI API
- **frontend**: Nginx с заглушкой (замените на React)

### Структура бэкенда

```
backend/
  app/
    main.py      # маршруты, точка входа
    models.py    # ORM-модели SQLAlchemy
    schemas.py   # Pydantic-схемы API
    db.py        # подключение к БД
    auth.py      # JWT + хеширование пароля
    deps.py      # зависимости FastAPI
  entrypoint.sh  # ожидание БД + запуск uvicorn
```

### Сущности

- **User** — профиль пользователя (email, имя, аватар, обложка, город, био).
- **Venue** — заведение (кальянная).
- **Room** — комнаты/столы внутри заведения (вместимость, цена, приватность).
- **Booking** — бронирование.
- **Favorite** — избранные заведения.
- **Post** — посты пользователя на стене.
- **Comment** — комментарии к постам.
- **PostLike** — лайки к постам.

### Основные возможности API

- Регистрация/авторизация через JWT.
- Профиль: чтение/обновление.
- Поиск заведений по фильтрам (город, цена, VIP, текстовый поиск).
- Комнаты/столы по заведению.
- Бронирования с проверкой пересечений по времени.
- Избранное.
- Стена пользователя (посты, лайки, комментарии).

## Примеры запросов

### Регистрация

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "123456", "display_name": "User"}'
```

### Логин

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=123456"
```

Ответ содержит JWT (`access_token`). Далее используйте его:

```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer <TOKEN>"
```

## Переменные окружения

- `DATABASE_URL` — строка подключения к PostgreSQL
- `JWT_SECRET` — секрет для подписи токенов
- `FRONTEND_URL` — адрес фронтенда (CORS)
- `APP_PORT` — порт API
