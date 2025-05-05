import json
import httpx
from telegram import Update
from telegram.ext import ContextTypes
from config import autoparse_data, selected_days, selected_sites, autoparse_points, saved_sites
from data_manager import save_parsed_result, PARSED_DATA_FILE, delete_point, save_points, delete_site, save_sites
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

    elif text == "Delete Time Point":
        if not autoparse_points:
            await update.message.reply_text("No time points available.")
        else:
            msg = "Enter the number(s) of time points you want to delete (comma-separated):\n"
            msg += "\n".join(f"{i+1}. {p['time']} {','.join(p['days'])} ({'repeating' if p['repeat'] else 'one-time'})"
                             for i, p in enumerate(autoparse_points))
            context.user_data['waiting_for_point_delete'] = True
            await update.message.reply_text(msg)

    elif text == "Time Points List":
        if not autoparse_points:
            await update.message.reply_text("No time points available.")
        else:
            lines = [f"{i+1}. {p['time']} {','.join(p['days'])} ({'repeating' if p['repeat'] else 'one-time'})" for i, p in enumerate(autoparse_points)]
            await update.message.reply_text("Time Points:\n" + "\n".join(lines))

    elif text == "Back":
        await update.message.reply_text("Going back...", reply_markup=main_menu())

    elif text == "Add Site":
        context.user_data['waiting_for_link'] = True
        await update.message.reply_text("Send the link(s) (you can send multiple, separated by commas)")

    elif text == "Parse":
        if not saved_sites:
            await update.message.reply_text("The sites list is empty.")
        else:
            await update.message.reply_text("Select sites for parsing:", reply_markup=site_selection_keyboard())

    elif text == "Sites List":
        if saved_sites:
            message = "Sites List:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(saved_sites))
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("The sites list is empty.")

    elif text == "Delete Site":
        if saved_sites:
            message = "Enter the number(s) of site(s) you want to delete (comma-separated):\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(saved_sites))
            context.user_data['waiting_for_delete_index'] = True
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("The sites list is empty.")

    elif context.user_data.get('waiting_for_link'):

        links = [link.strip() for link in text.split(',') if link.strip()]

        added, skipped, invalid, unreachable = [], [], [], []

        for link in links:

            # URL validation
            if not re.match(r'^https?://', link):
                invalid.append(link)
                continue

            if link in saved_sites:
                skipped.append(link)
                continue

            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(link)

                    if response.status_code == 200:
                        saved_sites.append(link)
                        added.append(link)
                    else:
                        unreachable.append(link)
            except Exception:
                unreachable.append(link)

        msg_parts = []

        if added:
            msg_parts.append("✅ Added site(s):\n" + "\n".join(added))
            save_sites()

        if skipped:
            msg_parts.append("ℹ️ Already exist:\n" + "\n".join(skipped))

        if invalid:
            msg_parts.append("❌ Invalid links:\n" + "\n".join(invalid))

        if unreachable:
            msg_parts.append("⚠️ Unreachable sites:\n" + "\n".join(unreachable))

        await update.message.reply_text("\n\n".join(msg_parts), reply_markup=parsing_menu())

        context.user_data['waiting_for_link'] = False

    elif context.user_data.get('waiting_for_delete_index'):
        indexes = text.split(',')
        removed, failed = [], []
        for idx in indexes:
            try:
                index = int(idx.strip()) - 1
                if 0 <= index < len(saved_sites):
                    site = saved_sites[index]
                    removed.append(site)
                else:
                    failed.append(idx.strip())
            except ValueError:
                failed.append(idx.strip())
        for site in removed:
            selected_sites.discard(site)
            delete_site(site)

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
        if saved_sites:
            with open("export_sites.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(saved_sites))
            await update.message.reply_document(document=open("export_sites.txt", "rb"))
        else:
            await update.message.reply_text("The sites list is empty.")

    elif text == "Export Time Points":
        if autoparse_points:
            lines = []
            for point in autoparse_points:
                line = f"{point['time']} {'/'.join(point['days'])} ({'repeating' if point['repeat'] else 'one-time'})"
                lines.append(line)
            with open("export_points.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            await update.message.reply_document(document=open("export_points.txt", "rb"))
        else:
            await update.message.reply_text("No time points available.")

    elif text == "Export Results":
        try:
            with open(PARSED_DATA_FILE, "r", encoding="utf-8") as f:
                parsed_data = json.load(f)

            lines = [f"[{entry['datetime']}] {entry['url']} → {entry['result']}" for entry in parsed_data]

            with open("export_results.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            await update.message.reply_document(document=open("export_results.txt", "rb"))
        except (FileNotFoundError, json.JSONDecodeError):
            await update.message.reply_text("Results file not found or empty.")

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

        # Get current text and markup
        current_text = query.message.text
        current_markup = query.message.reply_markup

        # Check if text or markup changed
        new_text = "Select point type:"
        new_markup = repeat_type_keyboard()

        if current_text != new_text or current_markup != new_markup:
            await query.edit_message_text(new_text, reply_markup=new_markup)

    elif query.data.startswith("repeat_type:"):
        rtype = query.data.split(":", 1)[1]
        autoparse_data['repeat_type'] = rtype
        context.user_data['waiting_for_time'] = True
        await query.edit_message_text("Enter time in HH:MM format")
