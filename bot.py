import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "8684462847:AAFuGHvKEXMyDe6vFBy0Xb3JA8hHFUdWrV8"

CATEGORIES = [
    "AMORE",
    "BASKET",
    "CALCIO",
    "CIBO",
    "TRAVEL",
    "FORMULA1",
    "MMA",
]

DB_PATH = "links.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT UNIQUE,
            category TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_link(user_id: int, url: str, category: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO links (user_id, url, category, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, url, category, datetime.now().isoformat()))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success


def get_links_by_category(category: str, user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT url, created_at
        FROM links
        WHERE category = ? AND user_id = ?
        ORDER BY id DESC
    """, (category, user_id))
    rows = cur.fetchall()
    conn.close()
    return rows


def is_tiktok_link(text: str) -> bool:
    text = text.lower()
    return "tiktok.com/" in text or "vm.tiktok.com/" in text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Mandami un link TikTok e ti farò scegliere la categoria."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if not is_tiktok_link(text):
        await update.message.reply_text(
            "Mandami un link TikTok valido."
        )
        return

    context.user_data["pending_url"] = text

    keyboard = []
    row = []
    for i, category in enumerate(CATEGORIES, start=1):
        row.append(InlineKeyboardButton(category, callback_data=f"cat:{category}"))
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Scegli la categoria per questo link:",
        reply_markup=reply_markup
    )


async def handle_category_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("cat:"):
        return

    category = data.split("cat:", 1)[1]
    url = context.user_data.get("pending_url")

    if not url:
        await query.edit_message_text(
            "Non trovo il link da salvare. Rimandamelo."
        )
        return

    user_id = query.from_user.id
    saved = save_link(user_id, url, category)

    if saved:
        await query.edit_message_text(
            f"Link salvato in {category} ✅\n\n{url}"
        )
    else:
        await query.edit_message_text(
            f"Questo link era già stato salvato prima in archivio ⚠️\n\n{url}"
        )

    context.user_data.pop("pending_url", None)


async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    user_id = update.effective_user.id
    rows = get_links_by_category(category, user_id)

    if not rows:
        await update.message.reply_text(f"Nessun link salvato in {category}.")
        return

    message_parts = [f"📂 {category}\n"]
    for idx, (url, created_at) in enumerate(rows[:50], start=1):
        message_parts.append(f"{idx}. {url}")

    await update.message.reply_text("\n".join(message_parts))


async def basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_category(update, context, "BASKET")


async def calcio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_category(update, context, "CALCIO")


async def cibo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_category(update, context, "CIBO")


async def travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_category(update, context, "TRAVEL")


async def formula1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_category(update, context, "FORMULA1")


async def mma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_category(update, context, "MMA")


async def amore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_category(update, context, "AMORE")


def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("basket", basket))
    app.add_handler(CommandHandler("calcio", calcio))
    app.add_handler(CommandHandler("cibo", cibo))
    app.add_handler(CommandHandler("travel", travel))
    app.add_handler(CommandHandler("formula1", formula1))
    app.add_handler(CommandHandler("mma", mma))
    app.add_handler(CommandHandler("amore", amore))

    app.add_handler(CallbackQueryHandler(handle_category_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot avviato...")
    app.run_polling()


if __name__ == "__main__":
    main()