# Интеграция с Backend API

Этот документ описывает необходимые эндпоинты для полной работы личного кабинета.

## Конфигурация

Установите URL бэкенда в файле `.env`:

```env
VITE_API_URL=http://localhost:3000/api
```

## Требуемые API эндпоинты

### 1. Пользователь

#### GET `/api/user/me`
Получить информацию о текущем пользователе

**Response:**
```json
{
  "id": "user-123",
  "name": "Иван Иванов",
  "email": "ivan@example.com",
  "avatarUrl": "https://example.com/avatar.jpg",
  "createdAt": "2025-01-01T00:00:00Z"
}
```

#### PATCH `/api/user/me`
Обновить профиль пользователя

**Request:**
```json
{
  "name": "Новое имя",
  "email": "new@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user-123",
    "name": "Новое имя",
    "email": "new@example.com",
    "avatarUrl": "https://example.com/avatar.jpg",
    "createdAt": "2025-01-01T00:00:00Z"
  }
}
```

#### POST `/api/user/avatar`
Загрузить аватар

**Request:** `multipart/form-data` с файлом в поле `avatar`

**Response:**
```json
{
  "success": true,
  "url": "https://example.com/avatars/new-avatar.jpg"
}
```

### 2. Задачи (Calendar)

#### GET `/api/tasks`
Получить все задачи пользователя

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "task-1",
      "title": "Встреча с командой",
      "description": "Обсуждение проекта",
      "start": "2025-11-14T10:00:00Z",
      "end": "2025-11-14T11:00:00Z",
      "userId": "user-123",
      "completed": false,
      "createdAt": "2025-11-13T00:00:00Z",
      "updatedAt": "2025-11-13T00:00:00Z"
    }
  ]
}
```

#### GET `/api/tasks/:id`
Получить задачу по ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "task-1",
    "title": "Встреча с командой",
    "description": "Обсуждение проекта",
    "start": "2025-11-14T10:00:00Z",
    "end": "2025-11-14T11:00:00Z",
    "userId": "user-123",
    "completed": false,
    "createdAt": "2025-11-13T00:00:00Z",
    "updatedAt": "2025-11-13T00:00:00Z"
  }
}
```

#### POST `/api/tasks`
Создать новую задачу

**Request:**
```json
{
  "title": "Новая задача",
  "description": "Описание задачи",
  "start": "2025-11-15T10:00:00Z",
  "end": "2025-11-15T11:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "task-2",
    "title": "Новая задача",
    "description": "Описание задачи",
    "start": "2025-11-15T10:00:00Z",
    "end": "2025-11-15T11:00:00Z",
    "userId": "user-123",
    "completed": false,
    "createdAt": "2025-11-14T00:00:00Z",
    "updatedAt": "2025-11-14T00:00:00Z"
  }
}
```

#### PATCH `/api/tasks/:id`
Обновить задачу

**Request:**
```json
{
  "title": "Обновленное название",
  "start": "2025-11-15T11:00:00Z",
  "end": "2025-11-15T12:00:00Z",
  "completed": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "task-1",
    "title": "Обновленное название",
    "description": "Обсуждение проекта",
    "start": "2025-11-15T11:00:00Z",
    "end": "2025-11-15T12:00:00Z",
    "userId": "user-123",
    "completed": true,
    "createdAt": "2025-11-13T00:00:00Z",
    "updatedAt": "2025-11-14T00:00:00Z"
  }
}
```

#### DELETE `/api/tasks/:id`
Удалить задачу

**Response:**
```json
{
  "success": true
}
```

### 3. Граф чатов

#### GET `/api/chats/graph`
Получить данные для графа всех чатов

**Response:**
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": "1",
        "label": "Общий чат",
        "type": "chat",
        "messageCount": 150,
        "createdAt": "2025-01-01T00:00:00Z"
      },
      {
        "id": "2",
        "label": "Проект А",
        "type": "chat",
        "messageCount": 89,
        "createdAt": "2025-01-05T00:00:00Z"
      },
      {
        "id": "3",
        "label": "Разработка",
        "type": "topic",
        "messageCount": 120
      },
      {
        "id": "4",
        "label": "Пользователь 1",
        "type": "user"
      }
    ],
    "edges": [
      {
        "source": "1",
        "target": "2",
        "type": "related",
        "weight": 5
      },
      {
        "source": "1",
        "target": "3",
        "type": "mentioned",
        "weight": 3
      },
      {
        "source": "4",
        "target": "1",
        "type": "replied",
        "weight": 10
      }
    ]
  }
}
```

**Типы узлов:**
- `chat` - чат/канал
- `topic` - тема обсуждения
- `user` - пользователь

**Типы связей:**
- `replied` - ответ на сообщение (зеленая линия)
- `mentioned` - упоминание/ссылка (синяя пунктирная линия)
- `related` - связанные темы (оранжевая линия)

#### GET `/api/chats/:id/connections`
Получить связи конкретного чата

**Response:**
```json
{
  "success": true,
  "data": {
    "nodes": [...],
    "edges": [...]
  }
}
```

## Обработка ошибок

Все ошибки возвращаются в следующем формате:

```json
{
  "error": "ErrorType",
  "message": "Описание ошибки",
  "statusCode": 400
}
```

## Интеграция в компонентах

### AvatarUpload
Раскомментируйте код загрузки в `front/src/components/profile/AvatarUpload.vue`:

```typescript
// Строки 57-61
const formData = new FormData()
formData.append('avatar', file)
const response = await apiService.uploadAvatar(file)
avatarUrl.value = response.url
```

### CalendarTask
Раскомментируйте код API в `front/src/components/profile/CalendarTask.vue`:

```typescript
// При создании задачи (строки ~179-183)
const response = await apiService.createTask(newEvent)
events.value.push(response.data)

// При обновлении (строки ~169-173)
await apiService.updateTask(eventForm.id!, eventForm)

// При удалении (строки ~194-196)
await apiService.deleteTask(eventForm.id!)

// При изменении дат (строки ~247-251)
await apiService.updateTask(id, { start, end })
```

### ChatGraph
Раскомментируйте код API в `front/src/components/profile/ChatGraph.vue`:

```typescript
// При обновлении графа (строки ~176-178)
const response = await apiService.getChatGraph()
// Обновите nodes и edges из response.data
```

## Пример полной интеграции

После реализации всех эндпоинтов:

1. Замените mock-данные в компонентах на реальные API вызовы
2. Добавьте обработку ошибок и loading состояния
3. Реализуйте авторизацию (токены в headers)
4. Добавьте WebSocket для real-time обновлений графа чатов (опционально)

## Безопасность

Не забудьте добавить:
- CORS настройки на бэкенде
- Валидацию файлов при загрузке аватара
- Проверку прав доступа к задачам и чатам
- Rate limiting для API эндпоинтов
