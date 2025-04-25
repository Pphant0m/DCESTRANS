import os
import csv
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# === Налаштування ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "123456789"))  # ← Замініть на свій ID

# === Стани ===
(
    CHOOSING, DATE, CITY, POST_OFFICE, FULL_NAME,
    PHONE, PARCEL_NUMBER, PACKAGE_COUNT, PACKAGE_TYPE
) = range(9)

MAIN_MENU = ReplyKeyboardMarkup(
    [["Внести дані"]],
    resize_keyboard=True
)

def get_date_keyboard():
    today = datetime.now().date()
    options = [today + timedelta(days=i) for i in range(3)]
    buttons = [[d.isoformat() for d in options[:2]], [options[2].isoformat(), "Інша дата"]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# === Обробники ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Обери дію:", reply_markup=MAIN_MENU)
    return CHOOSING

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Внести дані":
        await update.message.reply_text("Оберіть дату поїздки:", reply_markup=get_date_keyboard())
        return DATE
    await update.message.reply_text("Невідома дія. Спробуйте ще раз.")
    return CHOOSING

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_text = update.message.text.strip()
    if date_text == "Інша дата":
        await update.message.reply_text("Введіть дату вручну (у форматі YYYY-MM-DD):")
        return DATE

    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        context.user_data['date'] = date_text
        await update.message.reply_text("Місто доставки:")
        return CITY
    except ValueError:
        await update.message.reply_text("Невірний формат. Введіть ще раз у форматі YYYY-MM-DD:")
        return DATE

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text
    await update.message.reply_text("Номер відділення Нової Пошти:")
    return POST_OFFICE

async def get_post_office(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['post_office'] = update.message.text
    await update.message.reply_text("ПІБ отримувача:")
    return FULL_NAME

async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text("Мобільний номер телефону:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Порядковий номер посилки:")
    return PARCEL_NUMBER

async def get_parcel_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['parcel_number'] = update.message.text
    await update.message.reply_text("Кількість місць:")
    return PACKAGE_COUNT

async def get_package_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['package_count'] = update.message.text
    await update.message.reply_text("Тип пакування (мішок, коробка, інше):")
    return PACKAGE_TYPE

async def get_package_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['package_type'] = update.message.text

    trip_date = context.user_data['date']
    filename = f"{trip_date}.csv"

    file_exists = os.path.exists(filename)
    with open(filename, mode='a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                "Дата поїздки", "Місто", "Відділення", "ПІБ",
                "Телефон", "Номер посилки", "К-сть місць",
                "Пакування", "Дата запису"
            ])
        writer.writerow([
            context.user_data['date'],
            context.user_data['city'],
            context.user_data['post_office'],
            context.user_data['full_name'],
            context.user_data['phone'],
            context.user_data['parcel_number'],
            context.user_data['package_count'],
            context.user_data['package_type'],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])

    await update.message.reply_text("✅ Дані збережено у таблицю.")
    await update.message.reply_text("Готово! Оберіть наступну дію:", reply_markup=MAIN_MENU)

    await context.bot.send_document(
        chat_id=ADMIN_CHAT_ID,
        document=open(filename, "rb"),
        caption=f"\ud83d\udce6 Дані по рейсу {trip_date}"
    )

    return CHOOSING

# === Запуск бота ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            POST_OFFICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_post_office)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            PARCEL_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_parcel_number)],
            PACKAGE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_package_count)],
            PACKAGE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_package_type)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)

    print("\ud83d\udfe2 Shipment Bot is running with daily CSV export and date buttons...")
    app.run_polling()
