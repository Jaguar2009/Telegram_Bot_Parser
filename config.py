API_TOKEN = '7850307578:AAHA9LbwVyo2qa1JENLKvRdPsnGnysVVbGY'

saved_sites = []
selected_sites = set()
selected_days = set()
autoparse_data = {}
autoparse_points = []
user_chat_id = None
bot_context = None
schedule_loop = None

bot_instance = None

DAYS_OF_WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
DAY_MAP = {
    "Пн": "monday",
    "Вт": "tuesday",
    "Ср": "wednesday",
    "Чт": "thursday",
    "Пт": "friday",
    "Сб": "saturday",
    "Нд": "sunday"
}

