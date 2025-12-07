import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.error import Conflict
import os
import datetime
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Список исключений
exclude_articles = [
    "709598-1", "709596-1", "709597-1", "709421-1", "709540-1", "709301-1"
]


# Функция для обработки артикулов и количества
def process_article(article):
    article = str(article)

    if article in exclude_articles:
        return article, 1  # Артикул остаётся тем же, количество 1

    if article.count('-') == 2:
        parts = article.split('-')
        return parts[0] + '-' + parts[1], int(parts[2])  # Артикул и количество

    elif article.count('-') == 1:
        parts = article.split('-')
        return parts[0], int(parts[1])  # Артикул и количество

    else:
        return article, 1  # Артикул и количество 1


# Обработка Excel файла
def handle_excel(file_path):
    try:
        logger.info(f"Начало обработки файла: {file_path}")
        df = pd.read_excel(file_path)
        logger.info(f"Файл загружен, строк: {len(df)}")

        # Проверяем наличие необходимой колонки
        if 'Артикул продавца' not in df.columns:
            raise ValueError("В файле отсутствует колонка 'Артикул продавца'")

        # Применяем функцию к колонке 'Артикул продавца' и преобразуем результат в несколько колонок
        df[['Артикул', 'Количество']] = df['Артикул продавца'].apply(
            lambda x: pd.Series(process_article(x))
        )

        # Группировка по артикулу и подсчёт суммы по количеству
        grouped_df = df.groupby('Артикул', as_index=False)['Количество'].sum()
        logger.info(f"Обработано уникальных артикулов: {len(grouped_df)}")

        # Формируем текстовый вывод
        output = "\n".join([f"{row['Артикул']} {row['Количество']}шт" for _, row in grouped_df.iterrows()])

        logger.info("Файл успешно обработан")
        return output
    except Exception as e:
        logger.error(f"Ошибка при обработке Excel файла: {e}")
        raise


# Сохранение истории
def save_history(report, history_file='history.txt'):
    try:
        with open(history_file, 'a', encoding='utf-8') as f:
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{date} - \n{report}\n\n")
        logger.info(f"История сохранена в {history_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении истории: {e}")


# Загрузка отчета и отправка пользователю
async def download_report(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id
        logger.info(f"Пользователь {user_id} запросил загрузку отчета")
        # Просим пользователя загрузить Excel файл
        await update.message.reply_text('Пожалуйста, отправьте Excel файл для обработки.')
    except Exception as e:
        logger.error(f"Ошибка в download_report: {e}")
        await update.message.reply_text('Произошла ошибка. Попробуйте позже.')


# Обработка документа
async def handle_document(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id
        file_name = update.message.document.file_name
        logger.info(f"Пользователь {user_id} отправил файл: {file_name}")

        file = await update.message.document.get_file()

        # Проверка mime_type
        if update.message.document.mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            logger.info(f"Начало загрузки файла {file_name}")
            # Загружаем файл в нужное место
            await file.download_to_drive('temp_report.xlsx')
            logger.info(f"Файл {file_name} загружен")

            # Обрабатываем Excel файл
            report = handle_excel('temp_report.xlsx')

            # Сохраняем результат в историю
            save_history(report)

            # Отправляем результат пользователю
            await update.message.reply_text(f"Результат:\n{report}")
            logger.info(f"Результат отправлен пользователю {user_id}")
            
            # Удаляем временный файл
            try:
                os.remove('temp_report.xlsx')
                logger.info("Временный файл удален")
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл: {e}")
        else:
            logger.warning(f"Пользователь {user_id} отправил неподдерживаемый тип файла: {update.message.document.mime_type}")
            await update.message.reply_text("Пожалуйста, отправьте Excel файл (.xlsx).")
    except ValueError as e:
        logger.error(f"Ошибка валидации в handle_document: {e}")
        await update.message.reply_text(f"Ошибка обработки файла: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка в handle_document: {e}")
        await update.message.reply_text('Произошла ошибка при обработке файла. Попробуйте позже.')


# Показать историю
async def show_history(update: Update, context: CallbackContext):
    # Отправляем историю отчетов
    try:
        user_id = update.effective_user.id
        logger.info(f"Пользователь {user_id} запросил историю")
        with open('history.txt', 'r', encoding='utf-8') as file:
            history = file.read()
            if history:
                # Telegram имеет лимит на длину сообщения (4096 символов)
                if len(history) > 4000:
                    logger.info(f"История слишком длинная ({len(history)} символов), отправляются последние записи")
                    # Отправляем последние записи, если история слишком длинная
                    lines = history.split('\n')
                    recent_history = '\n'.join(lines[-50:])  # Последние 50 строк
                    await update.message.reply_text(f"История отчетов (последние записи):\n{recent_history}")
                else:
                    await update.message.reply_text(f"История отчетов:\n{history}")
                logger.info(f"История отправлена пользователю {user_id}")
            else:
                logger.info("История пуста")
                await update.message.reply_text("История пуста.")
    except FileNotFoundError:
        logger.warning("Файл истории не найден")
        await update.message.reply_text("История не найдена.")
    except Exception as e:
        logger.error(f"Ошибка в show_history: {e}")
        await update.message.reply_text('Произошла ошибка при загрузке истории.')


# Главная функция
async def start(update: Update, context: CallbackContext):
    try:
        # Кнопки для взаимодействия
        button_list = [
            [KeyboardButton("Загрузить отчет"), KeyboardButton("История")]
        ]
        reply_markup = ReplyKeyboardMarkup(button_list, resize_keyboard=True)
        await update.message.reply_text('Привет! Выберите одну из опций:', reply_markup=reply_markup)
        logger.info(f"Пользователь {update.effective_user.id} запустил бота")
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")


# Обработчик ошибок
async def error_handler(update: object, context: CallbackContext) -> None:
    """Обработчик ошибок для всех необработанных исключений."""
    error = context.error
    
    # Если это конфликт с другим экземпляром бота
    if isinstance(error, Conflict):
        logger.warning("Обнаружен конфликт: возможно, запущено несколько экземпляров бота")
        logger.warning("Убедитесь, что запущен только один экземпляр бота")
        # Для Conflict не логируем как ошибку, это ожидаемое поведение
        return
    
    # Для остальных ошибок логируем
    logger.error(f"Exception while handling an update: {error}", exc_info=error)
    
    # Если есть update и это сообщение, отправляем пользователю уведомление
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                'Произошла ошибка при обработке запроса. Попробуйте позже.'
            )
        except Exception:
            pass  # Игнорируем ошибки при отправке сообщения об ошибке


def main():
    logger.info("Инициализация бота...")
    # Получаем токен из переменных окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в переменных окружения!")
        raise ValueError("TELEGRAM_BOT_TOKEN должен быть установлен в переменных окружения")

    logger.info("Токен получен, создание приложения...")
    # Создаем объект Application
    application = Application.builder().token(token).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    logger.info("Обработчик команды /start зарегистрирован")

    # Обработка нажатий на кнопки
    application.add_handler(MessageHandler(filters.Regex('Загрузить отчет'), download_report))
    application.add_handler(MessageHandler(filters.Regex('История'), show_history))
    logger.info("Обработчики кнопок зарегистрированы")

    # Обработка документов
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    logger.info("Обработчик документов зарегистрирован")

    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    logger.info("Обработчик ошибок зарегистрирован")

    # Запуск бота
    logger.info("Бот запущен и готов к работе")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Игнорируем накопленные обновления при запуске
        )
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки, завершение работы бота...")
    except Exception as e:
        logger.error(f"Критическая ошибка при работе бота: {e}")
        raise


if __name__ == '__main__':
    main()
