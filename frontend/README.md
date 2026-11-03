# EMBICO Platform - Frontend

Фронтенд приложение для платформы EMBICO (клиника ЭКО).

## Технологический стек

- **React 18** + **TypeScript**
- **Vite** - сборщик и dev-сервер
- **Ant Design** - UI библиотека
- **React Router** - маршрутизация
- **TanStack Query (React Query)** - управление серверным состоянием
- **Axios** - HTTP клиент
- **i18next** - интернационализация (русский и казахский)
- **React Hook Form** + **Zod** - работа с формами
- **dayjs** - работа с датами

## Требования

- Node.js >= 18
- npm >= 9

## Установка и запуск

### 1. Установка зависимостей

```bash
cd frontend
npm install
```

### 2. Настройка окружения

Создайте файл `.env` в корне папки `frontend/` (уже создан):

```env
VITE_API_URL=http://localhost:8000
```

### 3. Запуск dev-сервера

```bash
npm run dev
```

Приложение будет доступно по адресу: **http://localhost:5173**

### 4. Сборка для продакшена

```bash
npm run build
```

Собранные файлы будут в папке `dist/`

### 5. Предпросмотр production сборки

```bash
npm run preview
```

## Структура проекта

```
frontend/
├── src/
│   ├── api/              # API клиенты (axios)
│   │   ├── client.ts     # Настройка axios
│   │   ├── auth.ts       # API авторизации
│   │   └── patients.ts   # API пациенток
│   ├── components/       # Переиспользуемые компоненты
│   │   ├── layout/       # Компоненты layout
│   │   │   ├── MainLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   └── ProtectedRoute.tsx
│   ├── pages/            # Страницы приложения
│   │   ├── Login.tsx
│   │   ├── Today.tsx
│   │   ├── Patients/
│   │   ├── Cycles/
│   │   ├── Lab/
│   │   ├── Embryos/
│   │   ├── Documents/
│   │   ├── Team/
│   │   └── Settings/
│   ├── context/          # React контексты
│   │   └── AuthContext.tsx
│   ├── hooks/            # Custom hooks
│   ├── i18n/             # Интернационализация
│   │   ├── locales/
│   │   │   ├── ru.json
│   │   │   └── kk.json
│   │   └── index.ts
│   ├── types/            # TypeScript типы
│   │   └── index.ts
│   ├── utils/            # Утилиты
│   │   └── auth.ts
│   ├── App.tsx           # Главный компонент
│   └── main.tsx          # Точка входа
├── .env                  # Переменные окружения
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Основные функции

### Авторизация

Вход в систему через JWT токены:

- Страница: `/login`
- Email: `admin@embico.kz`
- Пароль: `changeme123`

После входа токен сохраняется в `localStorage` и автоматически добавляется ко всем запросам.

### Навигация

**Основное меню:**
- 🗓️ Рабочий день (`/today`) - заглушка
- 👥 Пациенты (`/patients`) - CRUD операции
- 🔄 Циклы (`/cycles`) - заглушка
- 🧪 Лаборатория (`/lab`) - заглушка
- 🦠 Эмбрионы (`/embryos`) - заглушка
- 📄 Документы (`/documents`) - заглушка

**Служебное меню:**
- 👨‍⚕️ Команда (`/team`) - заглушка
- ⚙️ Настройки (`/settings`) - заглушка

### Пациенты

**Реализовано:**
- ✅ Список пациенток с поиском и пагинацией
- ✅ Карточка пациентки (просмотр)
- ✅ Создание новой пациентки
- ✅ Редактирование данных пациентки
- ✅ Удаление пациентки

**Маршруты:**
- `/patients` - список
- `/patients/new` - создание
- `/patients/:id` - карточка
- `/patients/:id/edit` - редактирование

### Интернационализация

Приложение поддерживает два языка:
- 🇷🇺 Русский (по умолчанию)
- 🇰🇿 Казахский

Переключатель языка находится в верхней панели (справа).

## Стилизация

Используется тема Ant Design с кастомизацией под дизайн EMBICO:

```typescript
{
  colorPrimary: '#004598',    // Основной синий
  colorSuccess: '#276b55',    // Зелёный
  colorWarning: '#8c5c23',    // Оранжевый
  colorError: '#a13f41',      // Красный
  borderRadius: 5,
  fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif',
}
```

## Взаимодействие с API

### Axios конфигурация

Базовый URL: `http://localhost:8000` (из `.env`)

Автоматически добавляется:
- `Authorization: Bearer <token>` заголовок
- Обработка 401 ошибок (перенаправление на `/login`)

### React Query

Все API запросы кэшируются и управляются через React Query:

```typescript
const { data, isLoading } = useQuery({
  queryKey: ['patients', page, search],
  queryFn: () => patientsApi.getPatients({ skip, limit, search }),
});
```

## Разработка

### Полезные команды

```bash
# Запуск dev-сервера
npm run dev

# Проверка типов TypeScript
npm run type-check

# Сборка
npm run build

# Предпросмотр сборки
npm run preview

# Линтинг (если настроен)
npm run lint
```

### Добавление новой страницы

1. Создайте компонент в `src/pages/`
2. Добавьте маршрут в `src/App.tsx`
3. Добавьте переводы в `src/i18n/locales/`
4. Добавьте пункт меню в `src/components/layout/Sidebar.tsx` (если нужно)

### Добавление API метода

1. Создайте файл в `src/api/` (например, `cycles.ts`)
2. Добавьте типы в `src/types/index.ts`
3. Используйте с React Query в компонентах

## Следующие шаги

После запуска фронтенда можно приступить к реализации остальных разделов:

1. **Циклы ЭКО** - полный клинический путь
2. **Мониторинг стимуляции** - визиты, триггер, графики
3. **Эмбриология** - оценка эмбрионов, time-lapse
4. **Документы** - протоколы циклов
5. **Аналитика** - статистика клиники
6. **Настройки** - ML-модели, импорт данных

## Помощь

Если возникли проблемы:

1. Убедитесь, что бэкенд запущен на `http://localhost:8000`
2. Проверьте консоль браузера на наличие ошибок
3. Проверьте Network tab для отладки API запросов
4. Убедитесь, что CORS настроен в бэкенде
