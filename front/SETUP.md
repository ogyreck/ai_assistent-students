# Установка и запуск StudAssis Frontend

## Быстрый старт

```bash
# 1. Установить зависимости
npm install

# 2. Запустить dev сервер
npm run dev
```

Приложение откроется на `http://localhost:5173`

## Настройка API

Все API запросы настраиваются через файл `.env`:

```bash
# Скопируйте пример
cp .env.example .env

# Измените адрес API
VITE_API_BASE_URL=http://localhost:8000
```

## Структура проекта

```
src/
├── assets/          # Изображения (лого, фон, референсы)
├── components/      # Vue компоненты
│   ├── Sidebar.vue  # Боковая панель с проектами и чатами
│   └── ChatView.vue # Компонент чата с сообщениями
├── views/
│   └── MainView.vue # Главная страница
├── stores/
│   └── app.ts       # Pinia store (состояние приложения)
├── types/
│   └── index.ts     # TypeScript типы
├── utils/
│   ├── api.ts       # API клиент
│   └── storage.ts   # Утилиты для localStorage
├── config/
│   └── api.ts       # Конфигурация API endpoints
└── router/
    └── index.ts     # Vue Router
```

## Возможности

### localStorage
Приложение автоматически сохраняет:
- **userId** - уникальный ID пользователя (генерируется автоматически)
- **userToken** - токен пользователя
- **currentChatId** - ID активного чата
- **currentProjectId** - ID активного проекта

### Управление состоянием
Используется Pinia store (`src/stores/app.ts`) для:
- Управления проектами
- Управления чатами
- Хранения сообщений
- Синхронизации с localStorage

### API конфигурация
Все endpoints определены в `src/config/api.ts`:
- auth: login, register, logout
- chat: send, history
- projects: CRUD операции

## Команды разработки

```bash
# Dev сервер с hot-reload
npm run dev

# Type-checking
npm run type-check

# Build для production
npm run build

# Lint
npm run lint
```

## Дизайн

Приложение использует:
- Градиентный фон (голубой → желтый → оранжевый)
- Белая боковая панель слева
- Область чата по центру
- Лого "SA" в хедере

Все изображения референсов находятся в `src/assets/`
