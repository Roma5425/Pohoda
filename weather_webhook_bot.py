from datetime import time
from telegram.ext import MessageHandler, filters, CallbackContext
import plotly.graph_objs as go
from translitua import translit, RussianSimple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler
import matplotlib.pyplot as plt
from io import BytesIO
import aiohttp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# 🔧 ВСТАВ СВІЙ API KEY ТУТ
WEATHER_API_KEY = "a3c564f1bb164e2fa31182534253107"
BOT_TOKEN = "7602321117:AAEfDXsoD2OYrPYWAmUIYSDtw1H8IFFGMuA"

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
    """
    Повертає перекладений текст за ключем та мовою користувача.
    Якщо переклад для мови не знайдено, використовує українську (uk).
    """
    lang_code_short = user_language_code.split('_')[0].lower()

    lang_dict = TRANSLATIONS.get(lang_code_short, TRANSLATIONS['uk'])

    text = lang_dict.get(key, f"MISSING_TRANSLATION_KEY:{key}")

    try:
        formatted_text = text.format(**kwargs)
        return formatted_text
    except KeyError as e:
        print(f"ERROR: Missing placeholder for key '{e}' in translation for '{key}' in language '{lang_code_short}'")
        return text


# 🌤️ Отримати прогноз погоди
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


# --- Функції графіків ---
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


# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang_code = update.effective_user.language_code if update.effective_user else 'uk'

    # Надсилаємо перше привітальне повідомлення з короткою інформацією
    await update.message.reply_text(get_translated_text(user_lang_code, 'initial_welcome'), parse_mode="Markdown")

    keyboard = [
        [InlineKeyboardButton("Київ", callback_data='Київ')],
        [InlineKeyboardButton("Львів", callback_data='Львів')],
        [InlineKeyboardButton("Харків", callback_data='Харків')],
        [InlineKeyboardButton("Одеса", callback_data='Одеса')],
        [InlineKeyboardButton(get_translated_text(user_lang_code, 'choose_city_button'), callback_data='manual')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Надсилаємо друге повідомлення з запитом обрати місто
    await update.message.reply_text(get_translated_text(user_lang_code, 'greeting_start'), reply_markup=reply_markup)


# 📥 Обробка повідомлення
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang_code = update.effective_user.language_code if update.effective_user else 'uk'

    city = update.message.text.strip()
    await update.message.reply_text(get_translated_text(user_lang_code, 'searching_city', city_name=city),
                                    parse_mode="Markdown")

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


async def handle_city_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_lang_code = update.effective_user.language_code if update.effective_user else 'uk'

    city = query.data
    if city == "manual":
        await query.edit_message_text(get_translated_text(user_lang_code, 'manual_city_prompt'))
        return

    await query.edit_message_text(get_translated_text(user_lang_code, 'getting_forecast_for', city_name=city),
                                  parse_mode="Markdown")

    forecast, temp_data, error = await get_weather_forecast(translit(city), user_lang_code)

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


# 🧠 Запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_city_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот працює. Очікую повідомлення...")
    app.run_polling()