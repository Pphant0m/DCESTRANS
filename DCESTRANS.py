import os
import csv
from datetime import datetime
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

# === Обробники ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Обери дію:", reply_markup=MAIN_MENU)
    return CHOOSING

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Внести дані":
        await update.message.reply_text("Введіть дату поїздки (напр. 2025-04-30):")
        return DATE
    await update.message.reply_text("Невідома дія. Спробуйте ще раз.")
    return CHOOSING

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text.strip()
    await update.message.reply_text("Місто доставки:")
    return CITY

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

    # === Формуємо ім’я файлу по даті поїздки ===
    trip_date = context.user_data['date']
    filename = f"{trip_date}.csv"

    # === Чи потрібно створювати файл з заголовками ===
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

    # === Надсилаємо таблицю адміну ===
    await context.bot.send_document(
        chat_id=ADMIN_CHAT_ID,
        document=open(filename, "rb"),
        caption=f"📦 Дані по рейсу {trip_date}"
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

    print("🟢 Shipment Bot is running with daily CSV export...")
    app.run_polling()
