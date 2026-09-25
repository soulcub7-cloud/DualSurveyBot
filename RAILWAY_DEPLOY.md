# Размещение CT Assembly Learning Hub на Railway

## 1. GitHub

Создайте пустой приватный репозиторий `ct-assembly-learning-hub` без README и загрузите в него содержимое папки `enterprise-lms`.

Файл локальной базы `data/lms.db` исключён из GitHub, чтобы персональные данные студентов не попали в репозиторий.

## 2. Railway

1. Создайте новый проект через **Deploy from GitHub repo** и выберите репозиторий.
2. Railway автоматически использует `Dockerfile`.
3. Добавьте к сервису **Volume** с точкой подключения `/app/data`.
4. В разделе **Variables** добавьте:

```text
LMS_DB_PATH=/app/data/lms.db
LMS_COOKIE_SECURE=1
LMS_ADMIN_PHONE=+7XXXXXXXXXX
LMS_ADMIN_PASSWORD=уникальный_надёжный_пароль
LMS_INITIAL_PASSWORD=временный_пароль_для_пользователей
LMS_BOT_INTEGRATION_TOKEN=одинаковый_секретный_ключ_для_LMS_и_бота
```

5. Откройте **Settings → Networking → Generate Domain**.
6. Проверьте адрес `/api/health`: он должен вернуть `"ok": true` и `"version": "9.0"`.

После подключения Volume студенты, наставники, оценки и посещаемость сохраняются при повторных развёртываниях.

## Важно

- Не публикуйте файл `data/lms.db` в открытом репозитории.
- Не записывайте реальные пароли в GitHub — используйте только Railway Variables.
- Сразу после первого входа замените временный пароль администратора.
- Настройте резервное копирование Railway Volume.
