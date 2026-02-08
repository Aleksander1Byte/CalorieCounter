# Calorie Counter
[![CI](https://github.com/Aleksander1Byte/CalorieCounter/actions/workflows/flake8.yml/badge.svg)](https://github.com/Aleksander1Byte/CalorieCounter/actions/workflows/flake8.yml)
[![Deploy](https://github.com/Aleksander1Byte/CalorieCounter/actions/workflows/deploy.yml/badge.svg)](https://github.com/Aleksander1Byte/CalorieCounter/actions/workflows/deploy.yml)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

Проект реализован как Rest API на FastAPI с отдельным Telegram-ботом, взаимодействующим с backend по HTTP

## Что такое Calorie Counter?

Calorie Counter - сервис для измерения КБЖУ и микронутриентов блюд по текстовому описанию или изображению

## ⚙️ Реализованная функциональность

### Backend (FastAPI)
- REST API для асинхронной записи/чтения/удаления данных
- Изоляция данных между пользователями (доступ только к своим записям)
- Агрегация записей пользователя за день
- Воспроизводимые миграции через Alembic
- Таблицы моделей для БД через SQLAlchemy Core
- Валидация входных данных и обработка ошибок
- Анализ содержания блюда по тексту или картинке через внешнюю LLM
- Использование строго **Repository Pattern** + отсутствие ORM

### Клиент (Telegram Bot)
- Отдельный frontend-клиент, взаимодействующий с backend через HTTP
- Взаимодействие с данными строго через API
- Использование заголовков для аутентификации пользователя

## 🛠 Технологии

**Backend:**
- Python 3.10
- FastAPI
- PostgreSQL
- AsyncIO
- SQLAlchemy Core

**Frontend:**
- Telegram Bot (asyncio)
- httpx
- logging

**Инфраструктура и инструменты:**
- Docker, docker-compose
- Github Actions (CI/CD)
- flake8

## Как пользоваться ботом?
Найдите бота в Telegram: @CalorieMicroBot

## Основные команды:
| Команда  | Описание |
| ------------- | ------------- |
| /start  | Начать работу |
| /today  | Показать сумму КБЖУ за сегодня |
| /last  | Посмотреть последнюю запись |
| /delete_last  | Удалить последнюю запись |
| [Текст или изображение]  | Получить анализ КБЖУ и микронутриентов |

## Архитектура проекта
```text
                                   ┌──────────────────┐
                                   │   LLM (Gemma)    │
                                   └────────▲─────────┘
                                            │ async httpx
                                            │
┌─────────────────┐    REST API    ┌────────▼─────────┐     ┌──────────────┐
│   Telegram Bot  │ ◄────────────► │     FastAPI      │ ◄─► │   Database   │
│    (Frontend)   │                │    (Backend)     │     │ (PostgreSQL) │
└─────────────────┘                └──────────────────┘     └──────────────┘

```

## Автор
Aleksander1Byte

[GitHub](https://github.com/Aleksander1Byte) • [Telegram](https://t.me/aleksander1byte)
