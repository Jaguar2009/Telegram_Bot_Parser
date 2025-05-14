API_TOKEN = '7649548824:AAHRYb5QSJAqpc6nh8bj5BYSNc2ziersptQ'

selected_sites = set()
selected_days = set()
autoparse_data = {}
user_chat_id = None
bot_context = None
schedule_loop = None

bot_instance = None

DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

DAY_MAP = {
    "Mon": "monday",
    "Tue": "tuesday",
    "Wed": "wednesday",
    "Thu": "thursday",
    "Fri": "friday",
    "Sat": "saturday",
    "Sun": "sunday"
}
