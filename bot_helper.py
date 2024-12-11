import telebot 
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton 
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import logging
from database import init_db, add_user, add_task, get_tasks, delete_task, clear_tasks

bot = telebot.TeleBot("")

init_db()
logging.basicConfig(filename="logs.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

@bot.message_handler(commands=['start'])
def start_command(message):
    add_user(message.chat.id, message.chat.username)
    bot.send_message(message.chat.id, "Привет! Я бот-помощник. Напиши /help, чтобы узнать мои команды.")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, """
Мои команды:
/add_task - Добавить задачу
/view_task - Показать список задач
/delete_task - Удалить задачу
/clear_tasks - Очистить все задачи""")
    
@bot.message_handler(commands=['add_task'])
def add_task_command(message):
    bot.send_message(message.chat.id, "Введите текст задачи:")
    bot.register_next_step_handler(message, save_task)

def save_task(message):
    add_task(message.chat.id, message.text)
    bot.send_message(message.chat.id, f"Задача '{message.text}' добавлена!")

@bot.message_handler(commands=['view_task'])
def view_task_command(message):
    tasks = get_tasks(message.chat.id)
    if tasks:
        response = "Ваши задачи:\n" + "\n".join([f"{task[0]}. {task[1]}" for task in tasks])
    else:
        response = "У вас пока нет задач."
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['delete_task'])
def delete_task_command(message):
    tasks = get_tasks(message.chat.id)
    if not tasks:
        bot.send_message(message.chat.id, "У вас пока нет задач.")
        return
    
    markup = InlineKeyboardMarkup()
    for task in tasks:
        markup.add(InlineKeyboardButton(task[1], callback_data=f"delete_{task[0]}"))
    bot.send_message(message.chat.id, "Выберите задачу для удаления:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startwith("delete_"))
def delete_task_callback(call):
    task_id = int(call.data.split("_")[1])
    delete_task(task_id)
    bot.answer_callback_query(call.id, "Задача удалена!")
    bot.send_message(call.message.chat.id, "Задача успешно удалена.")

@bot.message_handler(commands=['clear_tasks'])
def clear_tasks_command(message):
    clear_tasks(message.chat.id)
    bot.send_message(message.chat.id, "Все задачи удалены!")

def send_daily_reminder():
    from database import get_tasks
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    conn.close()

    for user_id in users:
        user_id = user_id[0]
        tasks = get_tasks(user_id)
        if tasks:
            task_list = "\n".join([f"- {task[1]}" for task in tasks])
            bot.send_message(user_id, f"Ваши задачи на сегодня:\n{task_list}")
        else:
            bot.send_message(user_id, "Сегодня у вас нет задач!")
    
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_reminder, "cron", hour=9)
scheduler.start()

bot.polling()
