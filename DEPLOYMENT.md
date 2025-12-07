# Инструкция по развертыванию бота на сервере

## Требования
- Python 3.8 или выше
- pip

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` в корне проекта:
```bash
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

Токен можно получить у [@BotFather](https://t.me/BotFather) в Telegram.

3. Запустите бота:
```bash
python bot_wb.py
```

## Запуск на сервере (Linux)

### Вариант 1: Использование systemd

Создайте файл `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Bot для обработки Excel файлов
After=network.target

[Service]
Type=simple
User=ваш_пользователь
WorkingDirectory=/path/to/pythonProject
Environment="TELEGRAM_BOT_TOKEN=ваш_токен_бота"
ExecStart=/usr/bin/python3 /path/to/pythonProject/bot_wb.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

Проверка статуса:
```bash
sudo systemctl status telegram-bot
```

### Вариант 2: Использование screen/tmux

```bash
screen -S telegram-bot
cd /path/to/pythonProject
export TELEGRAM_BOT_TOKEN=ваш_токен_бота
python3 bot_wb.py
# Нажмите Ctrl+A, затем D для отсоединения
```

### Вариант 3: Использование nohup

```bash
cd /path/to/pythonProject
export TELEGRAM_BOT_TOKEN=ваш_токен_бота
nohup python3 bot_wb.py > bot.log 2>&1 &
```

## Переменные окружения

- `TELEGRAM_BOT_TOKEN` - обязательный токен бота от BotFather

## Функциональность

Бот обрабатывает Excel файлы (.xlsx) с колонкой "Артикул продавца" и:
- Извлекает артикулы и количество
- Группирует по артикулам
- Сохраняет историю обработки
- Позволяет просматривать историю

## Логирование

Все события логируются в консоль. При использовании systemd логи можно просмотреть:
```bash
sudo journalctl -u telegram-bot -f
```

