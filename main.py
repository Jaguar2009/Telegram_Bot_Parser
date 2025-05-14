from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import httpx
from selectolax.parser import HTMLParser
import schedule
import threading
from datetime import datetime
import asyncio

import config
from config import DAYS_OF_WEEK, selected_sites, API_TOKEN
from data_manager import save_parsed_result, save_points, load_points
from keyboards import main_menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.user_chat_id = update.effective_chat.id
    config.bot_context = context
    await update.message.reply_text("Welcome! Please choose an action:", reply_markup=main_menu())


async def parse_site(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            tree = HTMLParser(response.text)
            title = tree.css_first("title")
            return title.text(strip=True) if title else "[no title]"
    except Exception as e:
        return f"Error while parsing {url}: {e}"


async def run_autoparsing():
    if not config.user_chat_id or not config.bot_context:
        return

    now = datetime.now()
    weekday = DAYS_OF_WEEK[now.weekday()]
    current_time = now.strftime("%H:%M")
    points = load_points()

    for point in points[:]:  # create a copy of the list
        if current_time == point['time'] and weekday in point['days']:
            if not selected_sites:
                await config.bot_context.bot.send_message(
                    chat_id=config.user_chat_id,
                    text="[Auto-parsing] No sites selected."
                )
                continue

            parsed_results = []  # list of (url, title) tuples
            output_lines = []    # for user output

            for url in selected_sites:
                title = await parse_site(url)
                parsed_results.append((url, title))
                output_lines.append(f"{url} → {title}")  # avoid mixing with saving

            message = "[Auto-parsing]\n" + "\n".join(output_lines)
            await config.bot_context.bot.send_message(chat_id=config.user_chat_id, text=message)

            save_parsed_result(parsed_results)  # pass only clean tuples

            if not point['repeat']:
                points.remove(point)

    save_points(points)


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

    app = ApplicationBuilder().token(API_TOKEN).read_timeout(30).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Start auto-parsing
    try:
        main_loop = asyncio.get_running_loop()
    except RuntimeError:
        main_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(main_loop)

    schedule.every().minute.do(lambda: asyncio.run_coroutine_threadsafe(run_autoparsing(), main_loop))
    start_schedule_thread()

    app.run_polling()
