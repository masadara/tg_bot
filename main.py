import telebot
import requests
import logging
import json
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных из .env-файла
load_dotenv()

# Замените токен на ваш реальный токен
token = os.getenv('YOUR_BOT_TOKEN')  # Замените на ваш токен
bot = telebot.TeleBot(token)

# Хранилище задач (по пользователям)
todos = {}

# Путь к файлу для хранения задач
TODO_FILE = 'todos.json'

HELP = '''
Список доступных команд:
* /start - Начать взаимодействие с ботом
* Добавить задачу через кнопку
* Показать задачи через кнопку
* Удалить задачу через кнопку
* Установить напоминание через кнопку
* Поиск сборки чемпиона через кнопку
'''


# Функция для создания клавиатуры
def main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Добавить задачу"))
    keyboard.add(types.KeyboardButton("Показать задачи"))
    keyboard.add(types.KeyboardButton("Удалить задачу"))
    keyboard.add(types.KeyboardButton("Установить напоминание"))
    keyboard.add(types.KeyboardButton("Поиск сборки чемпиона"))
    keyboard.add(types.KeyboardButton("Помощь"))
    return keyboard


def load_todos():
    """Загружает задачи из JSON-файла."""
    try:
        with open(TODO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"{TODO_FILE} not found. Starting with an empty todo list.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {TODO_FILE}. Starting with an empty todo list.")
        return {}


def save_todos():
    """Сохраняет задачи в JSON-файл."""
    with open(TODO_FILE, 'w', encoding='utf-8') as f:
        json.dump(todos, f, ensure_ascii=False, indent=4)  # Сохраняем с правильной кодировкой
        logger.info(f"Tasks saved to {TODO_FILE}.")


# Загружаем задачи при старте бота
todos = load_todos()


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот для управления задачами.", reply_markup=main_menu_keyboard())
    logger.info(f"User {message.from_user.username} started the bot.")


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = str(message.chat.id)  # Получаем ID пользователя как строку

    if user_id not in todos:
        todos[user_id] = []  # Инициализируем список задач для нового пользователя

    if message.text == "Добавить задачу":
        msg = bot.send_message(message.chat.id, "Введите задачу:")
        bot.register_next_step_handler(msg, lambda m: process_add_task(m, user_id))

    elif message.text == "Показать задачи":
        show_tasks(user_id)

    elif message.text == "Удалить задачу":
        show_tasks(user_id, delete=True)

    elif message.text == "Установить напоминание":
        msg = bot.send_message(message.chat.id, "Введите дату и время напоминания в формате YYYY-MM-DD HH:MM:")
        bot.register_next_step_handler(msg, lambda m: process_set_reminder(m, user_id))

    elif message.text == "Поиск сборки чемпиона":
        msg = bot.send_message(message.chat.id, "Введите имя чемпиона:")
        bot.register_next_step_handler(msg, process_champion_build)

    elif message.text == "Помощь":
        bot.send_message(message.chat.id, HELP)


def process_add_task(message, user_id):
    task = message.text.strip()

    if task:  # Проверяем, что задача не пустая
        add_todo(user_id, task)  # Добавляем задачу для текущего пользователя
        bot.send_message(message.chat.id, f'Задача "{task}" добавлена на сегодня.')
        logger.info(f'User {message.from_user.username} added task: "{task}".')
    else:
        bot.send_message(message.chat.id, 'Задача не может быть пустой.')


def add_todo(user_id, task):
    todos[user_id].append(task)  # Добавляем задачу в список задач пользователя
    save_todos()  # Сохраняем изменения в файл


def show_tasks(user_id, delete=False):
    if not todos[user_id]:
        bot.send_message(user_id, 'Список задач пуст.')
        return

    tasks_list = '\n'.join([f'{i + 1}. [ ] {task}' for i, task in enumerate(todos[user_id])])

    if delete:
        msg = bot.send_message(user_id, f'Ваши задачи:\n{tasks_list}\n\nВведите номер задачи для удаления:')
        bot.register_next_step_handler(msg, lambda m: process_delete_task(m, user_id))
    else:
        bot.send_message(user_id, f'Ваши задачи:\n{tasks_list}')

    logger.info(f'User {user_id} requested to show tasks.')


def process_delete_task(message, user_id):
    try:
        task_number = int(message.text) - 1  # Преобразуем номер задачи в индекс (начинается с 0)

        if 0 <= task_number < len(todos[user_id]):
            removed_task = todos[user_id].pop(task_number)  # Удаляем задачу из списка
            save_todos()  # Сохраняем изменения в файл после удаления задачи
            bot.send_message(message.chat.id, f'Задача "{removed_task}" удалена.')
            logger.info(f'User {message.from_user.username} deleted task: "{removed_task}".')
        else:
            bot.send_message(message.chat.id, 'Неверный номер задачи.')
            logger.warning(f'User {user_id} tried to delete an invalid task number.')

    except ValueError:
        bot.send_message(message.chat.id, 'Пожалуйста, введите корректный номер задачи.')


def process_set_reminder(message, user_id):
    try:
        reminder_time_str = message.text.strip()
        reminder_time = datetime.strptime(reminder_time_str, "%Y-%m-%d %H:%M")

        msg = bot.send_message(message.chat.id, "Введите задачу для напоминания:")
        bot.register_next_step_handler(msg, lambda m: schedule_reminder(m, reminder_time, user_id))

    except ValueError:
        bot.send_message(message.chat.id, 'Неверный формат даты и времени. Используйте YYYY-MM-DD HH:MM.')


def schedule_reminder(message, reminder_time, user_id):
    task = message.text.strip()

    if task:  # Проверяем на пустую задачу
        scheduler.add_job(send_reminder, 'date', run_date=reminder_time, args=[user_id, task])
        bot.send_message(user_id, f'Напоминание для задачи "{task}" установлено на {reminder_time}.')
        logger.info(f'Reminder set for user {user_id}: "{task}" at {reminder_time}.')
    else:
        bot.send_message(user_id, 'Задача не может быть пустой.')


def send_reminder(chat_id, task):
    bot.send_message(chat_id=chat_id, text=f'Напоминание: {task}')
    logger.info(f'Sent reminder to user {chat_id}: "{task}".')


def process_champion_build(message):
    champion_name = message.text.strip()

    build_info = get_champion_build(champion_name)

    if build_info:
        bot.send_message(message.chat.id, build_info)
        logger.info(f'User {message.from_user.username} searched for champion build: "{champion_name}".')
    else:
        bot.send_message(message.chat.id, "Сборка не найдена.")
        logger.warning(f'No build found for champion: "{champion_name}".')


def get_champion_build(champion_name):
    url = f'https://mobalytics.gg/lol/champions/{champion_name.lower()}'

    try:
        response = requests.get(url)

        if response.status_code == 200:
            return f"Сборка для чемпиона {champion_name} доступна по ссылке: {url}"

    except Exception as e:
        logger.error(f"Error fetching champion build: {str(e)}")

    return None


scheduler = BackgroundScheduler()
scheduler.start()

if __name__ == '__main__':
    logger.info('Bot is starting...')
    bot.polling(none_stop=True)