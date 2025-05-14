import json
import httpx
from telegram import Update
from telegram.ext import ContextTypes
from config import autoparse_data, selected_days, selected_sites
from data_manager import save_parsed_result, PARSED_DATA_FILE, delete_point, save_points, save_sites, load_sites, \
    add_site, remove_site, load_points
from export_manager import export_sites_to_pdf, export_points_to_pdf, export_results_to_pdf
from keyboards import repeat_type_keyboard, day_selection_keyboard, site_selection_keyboard, export_menu, \
    autoparsing_menu, parsing_menu, main_menu
import re
from main import parse_site

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Parsing":
        await update.message.reply_text("Parsing Menu:", reply_markup=parsing_menu())

    elif text == "Autoparsing":
        await update.message.reply_text("Autoparsing Menu:", reply_markup=autoparsing_menu())

    elif text == "Create Time Point":
        selected_days.clear()
        await update.message.reply_text("Select weekdays:", reply_markup=day_selection_keyboard())

    elif context.user_data.get('waiting_for_time'):
        time_pattern = r"^([0-1][0-9]|2[0-3]):([0-5][0-9])$"
        if re.match(time_pattern, text):
            time = text.strip()
            # Зберігаємо час для нової точки
            autoparse_data['time'] = time

            # Створюємо точку часу
            point = {
                'time': time,
                'days': list(selected_days),
                'repeat': autoparse_data['repeat_type'] == 'repeating'
            }

            points = load_points()
            points.append(point)
            save_points(points)

            await update.message.reply_text(f"Time point {time} created successfully!", reply_markup=autoparsing_menu())
            context.user_data['waiting_for_time'] = False
        else:
            await update.message.reply_text("Invalid time format. Please use HH:MM format.")

    elif text == "Delete Time Point":
        points = load_points()
        if not points:
            await update.message.reply_text("No time points available.")
        else:
            msg = "Enter the number(s) of time points you want to delete (comma-separated):\n"
            msg += "\n".join(
                f"{i + 1}. {p['time']} {','.join(p['days'])} ({'repeating' if p['repeat'] else 'one-time'})"
                for i, p in enumerate(points))
            context.user_data['waiting_for_point_delete'] = True
            await update.message.reply_text(msg)

    elif context.user_data.get('waiting_for_point_delete'):
        points = load_points()
        indexes = text.split(',')
        removed = []
        failed = []
        indexes_to_remove = []
        # Перевіряємо введені номери і додаємо їх до списку на видалення
        for idx in indexes:
            try:
                index = int(idx.strip()) - 1  # Коригуємо індексацію
                if 0 <= index < len(points):
                    indexes_to_remove.append(index)  # Додаємо індекс в список
                    removed.append(f"{points[index]['time']} {','.join(points[index]['days'])}")
                else:
                    failed.append(idx.strip())  # Невірний індекс
            except ValueError:
                failed.append(idx.strip())  # Некоректне значення
        # Видаляємо точки з основного списку
        for index in sorted(indexes_to_remove, reverse=True):  # Видаляємо з кінця, щоб не змінювати індекси
            points.pop(index)
        # Зберігаємо оновлений список точок
        save_points(points)
        # Відповідаємо користувачеві
        msg = ""
        if removed:
            msg += "Removed time point(s):\n" + "\n".join(removed) + "\n"
        if failed:
            msg += "Failed to process numbers: " + ", ".join(failed)
        await update.message.reply_text(msg.strip(), reply_markup=autoparsing_menu())
        context.user_data['waiting_for_point_delete'] = False

    elif text == "Time Points List":
        points = load_points()
        if not points:
            await update.message.reply_text("No time points available.")
        else:
            lines = [f"{i + 1}. {p['time']} {','.join(p['days'])} ({'repeating' if p['repeat'] else 'one-time'})"
                     for i, p in enumerate(points)]
            await update.message.reply_text("Time Points:\n" + "\n".join(lines))

    elif text == "Back":
        await update.message.reply_text("Going back...", reply_markup=main_menu())

    elif text == "Add Site":
        context.user_data['waiting_for_link'] = True
        await update.message.reply_text("Send the link(s) (you can send multiple, separated by commas)")

    elif text == "Parse":
        sites = load_sites()
        if not sites:
            await update.message.reply_text("The sites list is empty.")
        else:
            await update.message.reply_text("Select sites for parsing:", reply_markup=site_selection_keyboard())

    elif text == "Sites List":
        sites = load_sites()
        if sites:
            message = "Sites List:\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sites))
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("The sites list is empty.")

    elif text == "Delete Site":
        sites = load_sites()
        if sites:
            message = "Enter the number(s) of site(s) you want to delete (comma-separated):\n" + "\n".join(
                f"{i + 1}. {s}" for i, s in enumerate(sites))
            context.user_data['waiting_for_delete_index'] = True
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("The sites list is empty.")

    elif context.user_data.get('waiting_for_link'):
        links = [link.strip() for link in text.split(',') if link.strip()]
        added, skipped, invalid, unreachable = [], [], [], []
        current_sites = load_sites()
        for link in links:
            if not re.match(r'^https?://', link):
                invalid.append(link)
                continue
            if link in current_sites:
                skipped.append(link)
                continue
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(link)
                    if response.status_code == 200:
                        add_site(link)
                        added.append(link)
                    else:
                        unreachable.append(link)
            except Exception:
                unreachable.append(link)
        msg_parts = []

        if added:
            msg_parts.append("✅ Added site(s):\n" + "\n".join(added))
        if skipped:
            msg_parts.append("ℹ️ Already exist:\n" + "\n".join(skipped))
        if invalid:
            msg_parts.append("❌ Invalid links:\n" + "\n".join(invalid))
        if unreachable:
            msg_parts.append("⚠️ Unreachable sites:\n" + "\n".join(unreachable))
        await update.message.reply_text("\n\n".join(msg_parts), reply_markup=parsing_menu())
        context.user_data['waiting_for_link'] = False

    elif context.user_data.get('waiting_for_delete_index'):
        sites = load_sites()
        indexes = text.split(',')
        removed, failed = [], []
        for idx in indexes:
            try:
                index = int(idx.strip()) - 1
                if 0 <= index < len(sites):
                    site = sites[index]
                    removed.append(site)
                else:
                    failed.append(idx.strip())
            except ValueError:
                failed.append(idx.strip())
        for site in removed:
            selected_sites.discard(site)
            remove_site(site)
        msg = ""
        if removed:
            msg += "Removed site(s):\n" + "\n".join(removed) + "\n"
        if failed:
            msg += "Failed to process numbers: " + ", ".join(failed)
        await update.message.reply_text(msg.strip(), reply_markup=parsing_menu())
        context.user_data['waiting_for_delete_index'] = False

    elif text == "Export":
        await update.message.reply_text("Export Menu:", reply_markup=export_menu())

    elif text == "Export Sites":
        pdf = export_sites_to_pdf()
        if pdf:
            await update.message.reply_document(document=open(pdf, "rb"))
        else:
            await update.message.reply_text("The site list is empty.")

    elif text == "Export Time Points":
        pdf = export_points_to_pdf()
        if pdf:
            await update.message.reply_document(document=open(pdf, "rb"))
        else:
            await update.message.reply_text("There are no auto-parsing time points.")

    elif text == "Export Results":
        pdf = export_results_to_pdf()
        if pdf:
            await update.message.reply_document(document=open(pdf, "rb"))
        else:
            await update.message.reply_text("There are no saved results.")

    else:
        await update.message.reply_text("Unknown command. Please use the buttons.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("toggle:"):
        site = query.data.split(":", 1)[1]
        if site in selected_sites:
            selected_sites.remove(site)
        else:
            selected_sites.add(site)
        await query.edit_message_reply_markup(reply_markup=site_selection_keyboard())

    elif query.data.startswith("toggle_day:"):
        day = query.data.split(":", 1)[1]
        if day in selected_days:
            selected_days.remove(day)
        else:
            selected_days.add(day)
        await query.edit_message_reply_markup(reply_markup=day_selection_keyboard())

    elif query.data == "parse_selected":
        if not selected_sites:
            await query.edit_message_text("No site selected for parsing.")
        else:
            results = []
            for url in selected_sites:
                result = await parse_site(url)
                results.append(f"{url} → {result}")
            await query.edit_message_text("Parsing results:\n\n" + "\n".join(results))
            save_parsed_result([(url, result) for url, result in zip(selected_sites, results)])

    elif query.data == "next_step_repeat":
        if not selected_days:
            await query.answer("Select at least one day!", show_alert=True)
            return
        autoparse_data['days'] = list(selected_days)
        # Оновлюємо текст і кнопки
        new_text = "Select point type:"
        new_markup = repeat_type_keyboard()
        await query.edit_message_text(new_text, reply_markup=new_markup)

    elif query.data.startswith("repeat_type:"):
        rtype = query.data.split(":", 1)[1]
        autoparse_data['repeat_type'] = rtype
        context.user_data['waiting_for_time'] = True
        await query.edit_message_text("Enter time in HH:MM format")
