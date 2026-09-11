# Установка версии 9 и связи с DualSurveyBot

## 1. Обновить LMS

Распакуйте `CT_Assembly_Learning_Hub_v9_Update.zip` и загрузите все файлы в
корень репозитория `ct-assembly-learning-hub` с заменой. Файл базы данных
загружать не нужно. Railway автоматически выполнит новое развёртывание, а
существующая база на Volume обновится при запуске.

## 2. Обновить бот

Распакуйте `DualSurveyBot_LMS_Integration_Update.zip` и загрузите все файлы в
корень репозитория `DualSurveyBot` с заменой. Интерфейс, вопросы и сохранённые
анкеты бота не меняются.

## 3. Создать общий секретный ключ

В PowerShell выполните:

```powershell
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$bytes = New-Object byte[] 32
$rng.GetBytes($bytes)
[Convert]::ToBase64String($bytes)
```

Скопируйте полученную строку. Не публикуйте её в GitHub.

## 4. Настроить Railway Variables

В сервисе LMS добавьте:

```text
LMS_BOT_INTEGRATION_TOKEN=полученная_строка
```

В сервисе DualSurveyBot добавьте:

```text
LMS_API_URL=https://ct-assembly-learning-hub-production.up.railway.app
LMS_BOT_INTEGRATION_TOKEN=та_же_полученная_строка
```

После сохранения переменных перезапустите оба сервиса.

## 5. Проверить

Заполните одну тестовую анкету в Telegram. Через несколько секунд откройте в
LMS карточку выбранного студента. В разделах «Текущий профиль компетенций» и
«История анкет наставников» должны появиться результаты. В электронном журнале
новая запись не создаётся.
