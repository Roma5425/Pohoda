from datetime import time, datetime
from telegram.ext import MessageHandler, filters, CallbackContext
import plotly.graph_objs as go
from translitua import translit, RussianSimple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Application
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ApplicationBuilder
import matplotlib.pyplot as plt
from io import BytesIO
import aiohttp
import os
import sys

# 🔧 ОТРИМУЄМО API KEY ТА ТОКЕН ЗІ ЗМІННИХ СЕРЕДОВИЩА
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# Базова перевірка для обов'язкових змінних середовища для розгортання
if not WEATHER_API_KEY:
    print("Критична помилка: Змінна середовища 'WEATHER_API_KEY' не знайдена.")
    sys.exit(1)
if not BOT_TOKEN:
    print("Критична помилка: Змінна середовища 'BOT_TOKEN' не знайдена.")
    sys.exit(1)
if not WEBHOOK_URL:
    print("Критична помилка: Змінна середовища 'WEBHOOK_URL' не знайдена. Вона потрібна для Webhooks.")
    sys.exit(1)

# --- Словник перекладів ---
TRANSLATIONS = {
    'uk': {
        'initial_welcome': "👋 Привіт! Я ваш особистий метеоролог Weather Online Bot! 🌤️\n\nЯ допоможу тобі отримати детальний прогноз погоди на 7 днів для будь-якого міста світу, а також покажу зручні графіки температури та вологості.",
        'greeting_start': "Обери місто нижче або введи його назву:",
        'searching_city': "🔎 Шукаю прогноз погоди для: *{city_name}*...",
        'forecast_for': "📍 Прогноз погоди для *{location_name}, {country_name}* на 7 днів:\n\n",
        'date_label': "📅 *{date}*",
        'condition_label': "🌤️ {condition}",
        'temperature_label': "🌡️ Температура: {min_temp}°C - {max_temp}°C (середня: {avg_temp}°C)",
        'humidity_label': "💧 Вологість: {humidity}%",
        'wind_label': "💨 Вітер: {wind} км/год",
        'uv_index_label': "☀️ УФ-індекс: {uv_index}",
        'chance_rain_label': "☂️ Ймовірність дощу: {chance_rain}%",
        'chance_snow_label': "❄️ Ймовірність снігу: {chance_snow}%",
        'sunrise_label': "⬆️ Схід сонця: {sunrise}",
        'sunset_label': "⬇️ Захід сонця: {sunset}\n\n",
        'error_data': "⚠️ Не вдалося отримати дані. Перевірте правильність назви міста.",
        'chart_temp_title': "Середня температура на 7 днів",
        'chart_humidity_title': "📈 Середня вологість на 7 днів",
        'chart_interactive_title': "📊 Інтерактивний графік: Температура та Вологість",
        'chart_temp_caption': "📊 Графік температури",
        'chart_humidity_caption': "💧 Графік вологості",
        'chart_interactive_caption': "🧠 Інтерактивний графік (відкрий у браузері)",
        'choose_city_button': "Інше місто 📝",
        'manual_city_prompt': "✍️ Введи назву міста вручну:",
        'getting_forecast_for': "🔎 Отримую прогноз для: *{city_name}*...",
        'xaxis_title': "Дата",
        'yaxis_title': "Значення",
        'temp_legend': 'Температура (°C)',
        'humidity_legend': 'Вологість (%)',
        'chart_interactive_caption_filename': "Графік_погоди.html",
        'hourly_weather_button': "Погодинна погода ⏰",
        'hourly_forecast_for': "Погодинний прогноз для *{location_name}*:",
        'hourly_details': "*{time}*: {temp}°C, {condition}, Вітер: {wind} км/год",
        'no_hourly_data': "Не вдалося отримати погодинний прогноз для цього міста.",
        'choose_date_hourly': "Оберіть дату для погодинного прогнозу:",
        'hourly_back_to_main_menu': "⬅️ Назад до меню міста",
        'hourly_forecast_caption': "📊 Погодинний прогноз",
        'hourly_chart_title': "Погодинна температура",
        'hourly_chart_caption': "📊 Графік погодинної температури",
        'additional_options_prompt': "Додаткові опції:",
        'what_next_prompt': "Що далі?",
    },
    'en': {
        'initial_welcome': "👋 Hello! I'm your personal meteorologist, Weather Online Bot! 🌤️\n\nI'll help you get a detailed 7-day weather forecast for any city in the world, and also show you convenient temperature and humidity charts.",
        'greeting_start': "Choose a city below or enter its name:",
        'searching_city': "🔎 Searching for weather forecast for: *{city_name}*...",
        'forecast_for': "📍 Weather forecast for *{location_name}, {country_name}* for 7 days:\n\n",
        'date_label': "📅 *{date}*",
        'condition_label': "🌤️ {condition}",
        'temperature_label': "🌡️ Temperature: {min_temp}°C - {max_temp}°C (average: {avg_temp}°C)",
        'humidity_label': "💧 Humidity: {humidity}%",
        'wind_label': "💨 Wind: {wind} km/h",
        'uv_index_label': "☀️ UV Index: {uv_index}",
        'chance_rain_label': "☂️ Chance of rain: {chance_rain}%",
        'chance_snow_label': "❄️ Chance of snow: {chance_snow}%",
        'sunrise_label': "⬆️ Sunrise: {sunrise}",
        'sunset_label': "⬇️ Sunset: {sunset}\n\n",
        'error_data': "⚠️ Failed to get data. Please check the city name.",
        'chart_temp_title': "Average Temperature for 7 Days",
        'chart_humidity_title': "📈 Average Humidity for 7 Days",
        'chart_interactive_title': "📊 Interactive Chart: Temperature & Humidity",
        'chart_temp_caption': "📊 Temperature Chart",
        'chart_humidity_caption': "💧 Humidity Chart",
        'chart_interactive_caption': "🧠 Interactive Chart (open in browser)",
        'choose_city_button': "Other city 📝",
        'manual_city_prompt': "✍️ Enter city name manually:",
        'getting_forecast_for': "🔎 Getting forecast for: *{city_name}*...",
        'xaxis_title': "Date",
        'yaxis_title': "Value",
        'temp_legend': 'Temperature (°C)',
        'humidity_legend': 'Humidity (%)',
        'chart_interactive_caption_filename': "Weather_Chart.html",
        'hourly_weather_button': "Hourly Weather ⏰",
        'hourly_forecast_for': "Hourly forecast for *{location_name}*:",
        'hourly_details': "*{time}*: {temp}°C, {condition}, Wind: {wind} km/h",
        'no_hourly_data': "Failed to get hourly forecast for this city.",
        'choose_date_hourly': "Choose a date for hourly forecast:",
        'hourly_back_to_main_menu': "⬅️ Back to city menu",
        'hourly_forecast_caption': "📊 Hourly forecast",
        'hourly_chart_title': "Hourly Temperature",
        'hourly_chart_caption': "📊 Hourly temperature chart",
        'additional_options_prompt': "Additional options:",
        'what_next_prompt': "What's next?",
    }
}

# Мапування кодів мов Telegram на коди мов WeatherAPI
WEATHERAPI_LANG_MAP = {
    'uk': 'uk', 'en': 'en', 'ru': 'ru', 'pl': 'pl', 'es': 'es', 'fr': 'fr', 'de': 'de',
    'pt': 'pt', 'ja': 'ja', 'ko': 'ko', 'it': 'it', 'nl': 'nl', 'th': 'th', 'vi': 'vi',
    'ar': 'ar', 'hi': 'hi', 'bn': 'bn', 'el': 'el', 'hu': 'hu', 'id': 'id', 'fa': 'fa',
    'tl': 'tl', 'tr': 'tr', 'zh': 'zh', 'zh_TW': 'zh_TW'
}

def get_translated_text(user_language_code: str, key: str, **kwargs) -> str:
    lang_code_short = user_language_code.split('_')[0].lower()
    lang_dict = TRANSLATIONS.get(lang_code_short, TRANSLATIONS['uk'])
    text = lang_dict.get(key, f"MISSING_TRANSLATION_KEY:{key}")
    try:
        formatted_text = text.format(**kwargs)
        return formatted_text
    except KeyError as e:
        print(f"ERROR: Missing placeholder for key '{e}' in translation for '{key}' in language '{lang_code_short}'")
        return text

async def get_weather_forecast(city, user_lang_code='uk'):
    api_lang = WEATHERAPI_LANG_MAP.get(user_lang_code.split('_')[0].lower(), 'en')
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=7&lang={api_lang}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None, None, get_translated_text(user_lang_code, 'error_data')
            data = await response.json()
            t_forecast_for = get_translated_text(user_lang_code, 'forecast_for',
                                                 location_name=data['location']['name'],
                                                 country_name=data['location']['country'])
            forecast = t_forecast_for
            dates = []
            temps = []
            humidities = []
            for day_data in data["forecast"]["forecastday"]:
                date = day_data["date"]
                day_details = day_data["day"]
                astro_details = day_data["astro"]
                condition = day_details["condition"]["text"]
                avg_temp = day_details["avgtemp_c"]
                max_temp = day_details["maxtemp_c"]
                min_temp = day_details["mintemp_c"]
                wind_kph = day_details["maxwind_kph"]
                humidity = day_details["avghumidity"]
                uv_index = day_details["uv"]
                daily_chance_of_rain = day_details["daily_chance_of_rain"]
                daily_chance_of_snow = day_details["daily_chance_of_snow"]
                sunrise = astro_details["sunrise"]
                sunset = astro_details["sunset"]
                forecast += (
                    get_translated_text(user_lang_code, 'date_label', date=date) + "\n" +
                    get_translated_text(user_lang_code, 'condition_label', condition=condition) + "\n" +
                    get_translated_text(user_lang_code, 'temperature_label', min_temp=min_temp, max_temp=max_temp,
                                         avg_temp=avg_temp) + "\n" +
                    get_translated_text(user_lang_code, 'humidity_label', humidity=humidity) + "\n" +
                    get_translated_text(user_lang_code, 'wind_label', wind=wind_kph) + "\n" +
                    get_translated_text(user_lang_code, 'uv_index_label', uv_index=uv_index) + "\n" +
                    get_translated_text(user_lang_code, 'chance_rain_label',
                                         chance_rain=daily_chance_of_rain) + "\n" +
                    get_translated_text(user_lang_code, 'chance_snow_label',
                                         chance_snow=daily_chance_of_snow) + "\n" +
                    get_translated_text(user_lang_code, 'sunrise_label', sunrise=sunrise) + "\n" +
                    get_translated_text(user_lang_code, 'sunset_label', sunset=sunset)
                )
                dates.append(date)
                temps.append(avg_temp)
                humidities.append(humidity)
            return forecast, (dates, temps, humidities), None

async def get_hourly_forecast_data(city, date_str, user_lang_code='uk'):
    api_lang = WEATHERAPI_LANG_MAP.get(user_lang_code.split('_')[0].lower(), 'en')
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=3&lang={api_lang}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None, None, get_translated_text(user_lang_code, 'error_data')
            data = await response.json()
            location_name = data['location']['name']
            target_day_data = None
            for day_data in data["forecast"]["forecastday"]:
                if day_data["date"] == date_str:
                    target_day_data = day_data
                    break
            if not target_day_data:
                return None, None, get_translated_text(user_lang_code, 'no_hourly_data')

            hourly_forecasts = []
            hourly_temps = []
            hourly_times = []

            for hour_data in target_day_data['hour']:
                full_datetime_str = hour_data['time']
                full_datetime_obj = datetime.strptime(full_datetime_str, '%Y-%m-%d %H:%M')

                if full_datetime_obj >= datetime.now():
                    time_only_str = full_datetime_obj.strftime('%H:%M')
                    temp = hour_data['temp_c']
                    condition = hour_data['condition']['text']
                    wind = hour_data['wind_kph']

                    hourly_forecasts.append(get_translated_text(user_lang_code, 'hourly_details',
                                                                time=time_only_str,
                                                                temp=temp,
                                                                condition=condition,
                                                                wind=wind))
                    hourly_temps.append(temp)
                    hourly_times.append(time_only_str)

            if not hourly_forecasts:
                return None, None, get_translated_text(user_lang_code, 'no_hourly_data')

            forecast_text = get_translated_text(user_lang_code, 'hourly_forecast_for', location_name=location_name) + "\n\n"
            forecast_text += "\n".join(hourly_forecasts)
            return forecast_text, (hourly_times, hourly_temps), None

def generate_humidity_chart(dates, humidities, user_lang_code='uk'):
    plt.figure(figsize=(8, 4))
    plt.plot(dates, humidities, marker='o', linestyle='-', color='mediumseagreen')
    plt.title(get_translated_text(user_lang_code, 'chart_humidity_title'))
    plt.xlabel(get_translated_text(user_lang_code, 'xaxis_title'))
    plt.ylabel(get_translated_text(user_lang_code, 'humidity_legend'))
    plt.grid(False)
    plt.xticks(rotation=45)
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    return buffer

def generate_interactive_chart(dates, temps, humidities, user_lang_code='uk'):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=temps, mode='lines+markers',
        name=get_translated_text(user_lang_code, 'temp_legend'),
        line=dict(color='skyblue')
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=humidities, mode='lines+markers',
        name=get_translated_text(user_lang_code, 'humidity_legend'),
        line=dict(color='mediumseagreen')
    ))
    fig.update_layout(
        title=get_translated_text(user_lang_code, 'chart_interactive_title'),
        xaxis_title=get_translated_text(user_lang_code, 'xaxis_title'),
        yaxis_title=get_translated_text(user_lang_code, 'yaxis_title'),
        hovermode='x unified'
    )
    buffer = BytesIO()
    html_bytes = fig.to_html(full_html=False, include_plotlyjs='cdn').encode()
    buffer.write(html_bytes)
    buffer.seek(0)
    return buffer

def generate_temp_chart(dates, temps, user_lang_code='uk'):
    plt.figure(figsize=(8, 4))
    plt.plot(dates, temps, marker='o', linestyle='-', color='skyblue')
    plt.title(get_translated_text(user_lang_code, 'chart_temp_title'))
    plt.xlabel(get_translated_text(user_lang_code, 'xaxis_title'))
    plt.ylabel(get_translated_text(user_lang_code, 'temp_legend'))
    plt.grid(False)
    plt.xticks(rotation=45)
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    return buffer

def generate_hourly_temp_chart(times, temps, user_lang_code='uk'):
    plt.figure(figsize=(10, 5))
    plt.plot(times, temps, marker='o', linestyle='-', color='purple')
    plt.title(get_translated_text(user_lang_code, 'hourly_chart_title'))
    plt.xlabel(get_translated_text(user_lang_code, 'xaxis_title'))
    plt.ylabel(get_translated_text(user_lang_code, 'temp_legend'))
    plt.grid(True)
    n = max(1, len(times) // 8)
    plt.xticks(times[::n], rotation=45, ha='right')
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    return buffer

def get_start_keyboard(user_lang_code: str):
    keyboard = [
        [InlineKeyboardButton("Київ", callback_data='Київ')],
        [InlineKeyboardButton("Львів", callback_data='Львів')],
        [InlineKeyboardButton("Харків", callback_data='Харків')],
        [InlineKeyboardButton("Одеса", callback_data='Одеса')],
        [InlineKeyboardButton(get_translated_text(user_lang_code, 'choose_city_button'), callback_data='manual')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang_code = update.effective_user.language_code if update.effective_user else 'uk'
    await update.message.reply_text(get_translated_text(user_lang_code, 'initial_welcome'), parse_mode="Markdown")
    reply_markup = get_start_keyboard(user_lang_code)
    await update.message.reply_text(get_translated_text(user_lang_code, 'greeting_start'), reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang_code = update.effective_user.language_code if update.effective_user else 'uk'
    city = update.message.text.strip()
    await update.message.reply_text(get_translated_text(user_lang_code, 'searching_city', city_name=city),
                                     parse_mode="Markdown")
    context.user_data['current_city'] = city
    forecast, temp_data, error = await get_weather_forecast(translit(city), user_lang_code)
    if error:
        await update.message.reply_text(error)
    else:
        await update.message.reply_text(forecast, parse_mode="Markdown")
        dates, temps, humidities = temp_data
        chart_image = generate_temp_chart(dates, temps, user_lang_code)
        await update.message.reply_photo(photo=chart_image,
                                         caption=get_translated_text(user_lang_code, 'chart_temp_caption'))
        humidity_chart = generate_humidity_chart(dates, humidities, user_lang_code)
        await update.message.reply_photo(photo=humidity_chart,
                                         caption=get_translated_text(user_lang_code, 'chart_humidity_caption'))
        interactive = generate_interactive_chart(dates, temps, humidities, user_lang_code)
        await update.message.reply_document(document=interactive, filename=get_translated_text(user_lang_code,
                                                                                                'chart_interactive_caption_filename'),
                                             caption=get_translated_text(user_lang_code, 'chart_interactive_caption'))
        keyboard = [
            [InlineKeyboardButton(get_translated_text(user_lang_code, 'hourly_weather_button'), callback_data=f'hourly_weather_{translit(city)}')],
            [InlineKeyboardButton(get_translated_text(user_lang_code, 'choose_city_button'), callback_data='manual')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(get_translated_text(user_lang_code, 'additional_options_prompt'), reply_markup=reply_markup)

async def handle_city_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_lang_code = update.effective_user.language_code if update.effective_user else 'uk'
    city_data = query.data
    if city_data == "manual":
        await query.edit_message_text(get_translated_text(user_lang_code, 'manual_city_prompt'))
        return
    context.user_data['current_city'] = city_data
    await query.edit_message_text(get_translated_text(user_lang_code, 'getting_forecast_for', city_name=city_data),
                                  parse_mode="Markdown")
    forecast, temp_data, error = await get_weather_forecast(translit(city_data), user_lang_code)
    if error:
        await context.bot.send_message(chat_id=query.message.chat.id, text=error)
    else:
        await context.bot.send_message(chat_id=query.message.chat.id, text=forecast, parse_mode="Markdown")
        dates, temps, humidities = temp_data
        chart = generate_temp_chart(dates, temps, user_lang_code)
        await context.bot.send_photo(chat_id=query.message.chat.id, photo=chart,
                                     caption=get_translated_text(user_lang_code, 'chart_temp_caption'))
        humidity_chart = generate_humidity_chart(dates, humidities, user_lang_code)
        await context.bot.send_photo(chat_id=query.message.chat.id, photo=humidity_chart,
                                     caption=get_translated_text(user_lang_code, 'chart_humidity_caption'))
        interactive = generate_interactive_chart(dates, temps, humidities, user_lang_code)
        await context.bot.send_document(chat_id=query.message.chat.id, document=interactive,
                                        filename=get_translated_text(user_lang_code,
                                                                      'chart_interactive_caption_filename'),
                                        caption=get_translated_text(user_lang_code, 'chart_interactive_caption'))
        keyboard = [
            [InlineKeyboardButton(get_translated_text(user_lang_code, 'hourly_weather_button'), callback_data=f'hourly_weather_{translit(city_data)}')],
            [InlineKeyboardButton(get_translated_text(user_lang_code, 'choose_city_button'), callback_data='manual')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=query.message.chat.id, text=get_translated_text(user_lang_code, 'additional_options_prompt'), reply_markup=reply_markup)

async def handle_hourly_weather_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_lang_code = update.effective_user.language_code if update.effective_user else 'uk'
    city = query.data.replace('hourly_weather_', '')
    context.user_data['current_city'] = city
    _, temp_data, error = await get_weather_forecast(city, user_lang_code)
    if error:
        await context.bot.send_message(chat_id=query.message.chat.id, text=error)
        return
    dates = temp_data[0]
    keyboard = []
    for date in dates[:3]:
        keyboard.append([InlineKeyboardButton(date, callback_data=f'show_hourly_{date}')])
    keyboard.append([InlineKeyboardButton(get_translated_text(user_lang_code, 'hourly_back_to_main_menu'), callback_data='back_to_main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=get_translated_text(user_lang_code, 'choose_date_hourly'),
        reply_markup=reply_markup
    )

async def handle_hourly_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_lang_code = update.effective_user.language_code if update.effective_user else 'uk'
    if query.data == 'back_to_main_menu':
        await query.edit_message_text(get_translated_text(user_lang_code, 'greeting_start'), reply_markup=get_start_keyboard(user_lang_code))
        return
    date_str = query.data.replace('show_hourly_', '')
    city = context.user_data.get('current_city')
    if not city:
        await query.edit_message_text(get_translated_text(user_lang_code, 'error_data'))
        return
    await query.edit_message_text(get_translated_text(user_lang_code, 'getting_forecast_for', city_name=city),
                                  parse_mode="Markdown")
    forecast_text, hourly_data, error = await get_hourly_forecast_data(translit(city), date_str, user_lang_code)
    if error:
        await context.bot.send_message(chat_id=query.message.chat.id, text=error)
    else:
        await context.bot.send_message(chat_id=query.message.chat.id, text=forecast_text, parse_mode="Markdown")
        times, temps = hourly_data
        hourly_chart_image = generate_hourly_temp_chart(times, temps, user_lang_code)
        await context.bot.send_photo(chat_id=query.message.chat.id, photo=hourly_chart_image,
                                     caption=get_translated_text(user_lang_code, 'hourly_chart_caption'))
    keyboard = [
        [InlineKeyboardButton(get_translated_text(user_lang_code, 'hourly_weather_button'), callback_data=f'hourly_weather_{translit(city)}')],
        [InlineKeyboardButton(get_translated_text(user_lang_code, 'choose_city_button'), callback_data='manual')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=query.message.chat.id, text=get_translated_text(user_lang_code, 'what_next_prompt'), reply_markup=reply_markup)

# Цей `app` об'єкт є ASGI-додатком, який буде обслуговувати Gunicorn/Uvicorn.
# Коллбек `application_startup` виконається при запуску додатка Uvicorn.
async def application_startup(application: Application):
    try:
        full_webhook_url = f"{WEBHOOK_URL}/telegram"
        await application.bot.set_webhook(url=full_webhook_url)
        print(f"✅ Telegram webhook set to: {full_webhook_url}")
    except Exception as e:
        print(f"❌ Failed to set Telegram webhook: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).post_init(application_startup).build()

# Додавання обробників знову після перезбірки `app` з `post_init`
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_city_button, pattern='^(Київ|Львів|Харків|Одеса|manual)$'))
app.add_handler(CallbackQueryHandler(handle_hourly_weather_button, pattern='^hourly_weather_.*$'))
app.add_handler(CallbackQueryHandler(handle_hourly_date_selection, pattern='^show_hourly_.*$|^back_to_main_menu$'))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
