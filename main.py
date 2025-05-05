from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import httpx
from selectolax.parser import HTMLParser
import schedule
import threading
from datetime import datetime
import asyncio

import config
from config import autoparse_points, DAYS_OF_WEEK, selected_sites, API_TOKEN
from data_manager import save_parsed_result, load_data
from keyboards import main_menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.user_chat_id = update.effective_chat.id
    config.bot_context = context
    await update.message.reply_text("Вітаю! Оберіть дію:", reply_markup=main_menu())


async def parse_site(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            tree = HTMLParser(response.text)
            title = tree.css_first("title")
            return title.text(strip=True) if title else "[немає заголовка]"
    except Exception as e:
        return f"Помилка при парсингу {url}: {e}"


async def run_autoparsing():
    if not config.user_chat_id or not config.bot_context:
        return

    now = datetime.now()
    weekday = DAYS_OF_WEEK[now.weekday()]
    current_time = now.strftime("%H:%M")

    for point in autoparse_points[:]:
        if current_time == point['time'] and weekday in point['days']:
            if not selected_sites:
                await config.bot_context.bot.send_message(
                    chat_id=config.user_chat_id,
                    text="[Автопарсинг] Немає вибраних сайтів."
                )
                continue

            results = []
            parsed_results = []

            for url in selected_sites:
                title = await parse_site(url)
                results.append(f"{url} → {title}")
                parsed_results.append((url, title))

            message = "[Автопарсинг]\n" + "\n".join(results)
            await config.bot_context.bot.send_message(chat_id=config.user_chat_id, text=message)
            save_parsed_result(parsed_results)

            if not point['repeat']:
                autoparse_points.remove(point)


def start_schedule_thread():
    loop = asyncio.new_event_loop()

    def run_loop():
        asyncio.set_event_loop(loop)

        async def periodic():
            while True:
                schedule.run_pending()
                await asyncio.sleep(1)

        loop.create_task(periodic())
        loop.run_forever()

    threading.Thread(target=run_loop, daemon=True).start()
    return loop


if __name__ == '__main__':
    from handlers import handle_callback, handle_message
    load_data()

    app = ApplicationBuilder().token(API_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Запуск автопарсингу
    try:
        main_loop = asyncio.get_running_loop()
    except RuntimeError:
        main_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(main_loop)

    schedule.every().minute.do(lambda: asyncio.run_coroutine_threadsafe(run_autoparsing(), main_loop))
    start_schedule_thread()

    app.run_polling()
