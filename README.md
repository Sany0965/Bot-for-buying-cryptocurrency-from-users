
# Cryptobot-YooMoney Exchange Bot 🤖💸

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Бот для обмена криптовалюты (USDT) через Cryptobot на фиатные средства с выводом на YooMoney.  
**Особенности**: автоматический расчет комиссии, проверка реквизитов, возврат средств.

---

## 🔍 Основные функции
- 💱 Обмен USDT → RUB через Cryptobot API
- 🏦 Вывод средств на YooMoney (с проверкой номера счета)
- 🔄 Возврат средств через крипто-чек при отмене операции
- 📊 Автоматический расчет комиссии (5%)
- 🛡 Валидация данных пользователя

## ⚙️ Технологии
- `Python 3.9+`
- `python-telegram-bot` (для работы с Telegram API)
- `requests` (HTTP-запросы к Cryptobot/YooMoney)
- `SQLite3` (хранение данных пользователей)
- `yoomoney` (для работы с YooMoney API)

---

## 🚀 Быстрый старт

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Конфигурация
1. Создайте `config.py` на основе примера:
```python
TELEGRAM_TOKEN = "ваш_токен_бота"
CRYPTOBOT_API_TOKEN = "ваш_токен_cryptobot"
YOUMONEY_OAUTH_TOKEN = "ваш_токен_юмани"
DB_PATH = "cryptobot.db"
```

2. Для получения токена YooMoney:
```python
from yoomoney import Authorize

Authorize(
    client_id="ВАШ_CLIENT_ID",
    redirect_uri="ВАШ_REDIRECT_URI",
    client_secret="ВАШ_CLIENT_SECRET",
    scope=["account-info", "operation-history", "payment-p2p"]  # Обязательный scope для P2P
)
```
**Инструкция по получению токенов**:  
📌 [YooMoney API Guide](https://github.com/Sany0965/YooMoney-)

---

## 🧩 Структура проекта
```
├── bot.py            # Основная логика бота
├── payments.py       # Работа с Cryptobot/YooMoney API
├── db.py             # База данных (SQLite3)
├── config.py         # Конфигурационные параметры
└── requirements.txt  # Зависимости
```

---

## ⚠️ Важные нюансы в боте
1. Требования к номеру счета YooMoney:
   - 16 цифр
   - Начинается с `4110`
   - Пример: `4110123456789000`

2. Комиссии:
   - 5% от суммы обмена
   - Возврат без комиссии

3. Для работы с Cryptobot:
   - Минимальная сумма: 0.1 USDT
   - Токен должен иметь права на создание чеков

---

## 📄 Лицензия
MIT License. Разработано при поддержке [@worpli](https://t.me/worpli).  
Скачивайте код в релизах репозитория

> **Note**  
> Перед запуском убедитесь, что все API-токены корректны и имеют необходимые права доступа.
```
