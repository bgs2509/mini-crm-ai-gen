# 📖 Примеры использования API

Практические примеры работы с API через curl команды.

## Требования

Для работы с примерами вам понадобится:
- `curl` установленный в системе
- Запущенный API сервер на `http://localhost:8000`
- Полученные токены и ID организации

---

## 1. 🔐 Регистрация и аутентификация

### Регистрация нового пользователя

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ivan@example.com",
    "password": "SecurePass123",
    "name": "Иван Петров",
    "organization_name": "ООО Рога и Копыта"
  }'
```

**Ответ:**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "ivan@example.com",
    "name": "Иван Петров"
  },
  "organization": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "ООО Рога и Копыта"
  }
}
```

> 💡 **Важно:** Сохраните `organization.id` для дальнейших запросов

### Вход в систему

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ivan@example.com",
    "password": "SecurePass123"
  }'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> 💡 **Сохраните токены:**
> ```bash
> export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
> export ORG_ID="660e8400-e29b-41d4-a716-446655440001"
> ```

### Обновление токена

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 2. 📇 Работа с контактами

### Создать контакт

```bash
curl -X POST "http://localhost:8000/api/v1/contacts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Алексей Смирнов",
    "email": "alexey@client.com",
    "phone": "+79161234567"
  }'
```

**Ответ:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Алексей Смирнов",
  "email": "alexey@client.com",
  "phone": "+79161234567",
  "created_at": "2025-01-15T10:00:00Z"
}
```

> 💡 Сохраните `id` контакта:
> ```bash
> export CONTACT_ID="770e8400-e29b-41d4-a716-446655440002"
> ```

### Получить список контактов

```bash
curl -X GET "http://localhost:8000/api/v1/contacts?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

### Поиск контактов

```bash
curl -X GET "http://localhost:8000/api/v1/contacts?search=Алексей" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

### Получить контакт по ID

```bash
curl -X GET "http://localhost:8000/api/v1/contacts/$CONTACT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

### Обновить контакт

```bash
curl -X PUT "http://localhost:8000/api/v1/contacts/$CONTACT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Алексей Смирнов",
    "email": "new@email.com",
    "phone": "+79167654321"
  }'
```

### Удалить контакт

```bash
curl -X DELETE "http://localhost:8000/api/v1/contacts/$CONTACT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

> ⚠️ **Важно:** Контакт можно удалить только если у него нет связанных сделок.

---

## 3. 💼 Работа со сделками

### Создать сделку

```bash
curl -X POST "http://localhost:8000/api/v1/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "770e8400-e29b-41d4-a716-446655440002",
    "title": "Поставка оборудования",
    "amount": 500000.00,
    "currency": "RUB",
    "stage": "qualification"
  }'
```

**Ответ:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "title": "Поставка оборудования",
  "amount": 500000.0,
  "currency": "RUB",
  "status": "new",
  "stage": "qualification",
  "contact_id": "770e8400-e29b-41d4-a716-446655440002",
  "created_at": "2025-01-15T10:30:00Z"
}
```

> 💡 Сохраните `id` сделки:
> ```bash
> export DEAL_ID="880e8400-e29b-41d4-a716-446655440003"
> ```

### Список сделок с фильтрацией

```bash
# Фильтр по статусу и сумме, сортировка по сумме (убывание)
curl -X GET "http://localhost:8000/api/v1/deals?status=in_progress&min_amount=100000&order_by=amount&order=desc" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

### Получить сделку по ID

```bash
curl -X GET "http://localhost:8000/api/v1/deals/$DEAL_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

### Обновить статус сделки

```bash
curl -X PATCH "http://localhost:8000/api/v1/deals/$DEAL_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "won",
    "stage": "closed"
  }'
```

> ⚠️ **Бизнес-правило:** Если статус `won`, сумма должна быть больше 0.

### Удалить сделку

```bash
curl -X DELETE "http://localhost:8000/api/v1/deals/$DEAL_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

---

## 4. ✅ Работа с задачами

### Создать задачу

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": "880e8400-e29b-41d4-a716-446655440003",
    "title": "Подготовить коммерческое предложение",
    "description": "Включить цены и условия доставки",
    "due_date": "2025-02-01"
  }'
```

**Ответ:**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "deal_id": "880e8400-e29b-41d4-a716-446655440003",
  "title": "Подготовить коммерческое предложение",
  "description": "Включить цены и условия доставки",
  "due_date": "2025-02-01",
  "is_done": false,
  "created_at": "2025-01-15T11:00:00Z"
}
```

> 💡 Сохраните `id` задачи:
> ```bash
> export TASK_ID="990e8400-e29b-41d4-a716-446655440004"
> ```

### Список задач по сделке

```bash
curl -X GET "http://localhost:8000/api/v1/tasks?deal_id=$DEAL_ID&only_open=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

### Получить задачу по ID

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

### Отметить задачу как выполненную

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "is_done": true
  }'
```

### Удалить задачу

```bash
curl -X DELETE "http://localhost:8000/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

---

## 5. 📝 Активности и таймлайн

### Получить таймлайн сделки

```bash
curl -X GET "http://localhost:8000/api/v1/deals/$DEAL_ID/activities" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

**Ответ:**
```json
{
  "items": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "deal_id": "880e8400-e29b-41d4-a716-446655440003",
      "author_id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "comment",
      "payload": {
        "text": "Клиент согласен с условиями, ждем подписания договора"
      },
      "created_at": "2025-01-15T12:00:00Z"
    },
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440006",
      "deal_id": "880e8400-e29b-41d4-a716-446655440003",
      "author_id": null,
      "type": "status_changed",
      "payload": {
        "old_status": "new",
        "new_status": "in_progress"
      },
      "created_at": "2025-01-15T10:35:00Z"
    }
  ],
  "total": 2
}
```

### Добавить комментарий

```bash
curl -X POST "http://localhost:8000/api/v1/deals/$DEAL_ID/activities" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "comment",
    "payload": {
      "text": "Клиент согласен с условиями, ждем подписания договора"
    }
  }'
```

> 💡 **Примечание:** Системные активности (изменение статуса, создание задач) создаются автоматически.

---

## 6. 📊 Аналитика

### Сводка по сделкам

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/deals/summary" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

**Ответ:**
```json
{
  "by_status": {
    "new": {
      "count": 15,
      "total_amount": 500000.0
    },
    "in_progress": {
      "count": 8,
      "total_amount": 350000.0
    },
    "won": {
      "count": 23,
      "total_amount": 1200000.0
    },
    "lost": {
      "count": 5,
      "total_amount": 150000.0
    }
  },
  "average_won_amount": 52173.91,
  "new_deals_last_30_days": 12
}
```

### Воронка продаж

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/deals/funnel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

**Ответ:**
```json
{
  "funnel": [
    {
      "stage": "qualification",
      "count": 25,
      "by_status": {
        "new": 15,
        "in_progress": 8,
        "won": 2
      },
      "conversion_rate": 100.0
    },
    {
      "stage": "proposal",
      "count": 18,
      "by_status": {
        "in_progress": 12,
        "won": 5,
        "lost": 1
      },
      "conversion_rate": 72.0
    },
    {
      "stage": "negotiation",
      "count": 12,
      "by_status": {
        "in_progress": 8,
        "won": 4
      },
      "conversion_rate": 66.67
    },
    {
      "stage": "closed",
      "count": 8,
      "by_status": {
        "won": 7,
        "lost": 1
      },
      "conversion_rate": 66.67
    }
  ]
}
```

---

## 🎯 Полный сценарий работы

Пример полного цикла работы с CRM:

```bash
# 1. Регистрация и получение токенов
REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "SecurePass123",
    "name": "Демо Пользователь",
    "organization_name": "Демо Компания"
  }')

export ORG_ID=$(echo $REGISTER_RESPONSE | jq -r '.organization.id')

# 2. Вход и получение токена
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "SecurePass123"
  }')

export TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# 3. Создание контакта
CONTACT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/contacts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Алексей Клиентов",
    "email": "alexey@client.com",
    "phone": "+79161234567"
  }')

export CONTACT_ID=$(echo $CONTACT_RESPONSE | jq -r '.id')

# 4. Создание сделки
DEAL_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "'$CONTACT_ID'",
    "title": "Продажа оборудования",
    "amount": 500000.00,
    "currency": "RUB",
    "stage": "qualification"
  }')

export DEAL_ID=$(echo $DEAL_RESPONSE | jq -r '.id')

# 5. Создание задачи
TASK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": "'$DEAL_ID'",
    "title": "Подготовить коммерческое предложение",
    "description": "Включить все детали",
    "due_date": "2025-02-01"
  }')

export TASK_ID=$(echo $TASK_RESPONSE | jq -r '.id')

# 6. Добавление комментария
curl -X POST "http://localhost:8000/api/v1/deals/$DEAL_ID/activities" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "comment",
    "payload": {
      "text": "Начата работа над сделкой"
    }
  }'

# 7. Обновление статуса сделки
curl -X PATCH "http://localhost:8000/api/v1/deals/$DEAL_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "stage": "proposal"
  }'

# 8. Получение аналитики
curl -X GET "http://localhost:8000/api/v1/analytics/deals/summary" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"

echo "✅ Полный сценарий выполнен успешно!"
```

---

## 🔍 Полезные команды

### Сохранить ответ в файл

```bash
curl -X GET "http://localhost:8000/api/v1/contacts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  -o contacts.json
```

### Показать заголовки ответа

```bash
curl -i -X GET "http://localhost:8000/api/v1/contacts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID"
```

### Форматированный JSON (требуется jq)

```bash
curl -s -X GET "http://localhost:8000/api/v1/contacts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID" \
  | jq '.'
```

### Обработка ошибок

```bash
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X GET "http://localhost:8000/api/v1/contacts/invalid-id" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-Id: $ORG_ID")

if [ $HTTP_CODE -eq 404 ]; then
  echo "Ресурс не найден"
elif [ $HTTP_CODE -eq 401 ]; then
  echo "Не авторизован"
else
  echo "Код ответа: $HTTP_CODE"
fi
```

---

## 📝 Примечания

- Все примеры используют переменные окружения `$TOKEN` и `$ORG_ID` для упрощения
- Замените UUID на реальные значения из ответов API
- Access token действителен 15 минут, используйте refresh token для обновления
- Для работы с jq установите его: `sudo apt-get install jq` (Linux) или `brew install jq` (macOS)
- Все даты должны быть в формате ISO 8601: `YYYY-MM-DD` или `YYYY-MM-DDTHH:MM:SSZ`

