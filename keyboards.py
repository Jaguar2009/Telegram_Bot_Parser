from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from config import saved_sites, selected_sites, selected_days, DAYS_OF_WEEK

def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Parsing"), KeyboardButton("Autoparsing")],
            [KeyboardButton("Export")]
        ], resize_keyboard=True
    )

def export_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Export Sites"), KeyboardButton("Export Time Points")],
            [KeyboardButton("Export Results")],
            [KeyboardButton("Back")]
        ], resize_keyboard=True
    )

def parsing_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Add Site"), KeyboardButton("Parse")],
            [KeyboardButton("Sites List"), KeyboardButton("Delete Site")],
            [KeyboardButton("Back")]
        ], resize_keyboard=True
    )

def autoparsing_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Create Time Point"), KeyboardButton("Time Points List")],
            [KeyboardButton("Delete Time Point")],
            [KeyboardButton("Back")]
        ], resize_keyboard=True
    )

def day_selection_keyboard():
    buttons = []
    for day in DAYS_OF_WEEK:
        checked = "✅" if day in selected_days else "⬜"
        buttons.append(InlineKeyboardButton(f"{checked} {day}", callback_data=f"toggle_day:{day}"))
    rows = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
    rows.append([InlineKeyboardButton("Next ▶️", callback_data="next_step_repeat")])
    return InlineKeyboardMarkup(rows)

def repeat_type_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔁 Repeating", callback_data="repeat_type:repeating"),
        InlineKeyboardButton("🕐 One-time", callback_data="repeat_type:once")
    ]])

def site_selection_keyboard():
    buttons = []
    for site in saved_sites:
        checked = "✅" if site in selected_sites else "⬜"
        buttons.append([InlineKeyboardButton(f"{checked} {site}", callback_data=f"toggle:{site}")])
    if saved_sites:
        buttons.append([InlineKeyboardButton("🔍 Parse Selected", callback_data="parse_selected")])
    return InlineKeyboardMarkup(buttons)
