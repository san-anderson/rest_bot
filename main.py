import telebot
from telebot import types
import re
from datetime import datetime, timedelta

bot = telebot.TeleBot('8187420980:AAFLfckBFdA8VsaeGVJQXhrLLvK7o_N1KeE')

menu = {
    'Страви': {
        'Вареники': {
            'price': 50,
            'photo': 'photos/varenyk.jpg'
        },
        'Деруни': {
            'price': 70,
            'photo': 'photos/deruny.jpg'
        },
        'Борщ': {
            'price': 60,
            'photo': 'photos/borshch.jpg'
        },
        'Солянка': {
            'price': 65,
            'photo': 'photos/solyanka.jpg'
        },
        'Холодник': {
            'price': 55,
            'photo': 'photos/holodnik.jpg'
        },
        'Піца Маргарита': {
            'price': 120,
            'photo': 'photos/pizza_margarita.jpg'
        },
        'Піца 4 Сири': {
            'price': 150,
            'photo': 'photos/pizza_4cheese.jpg'
        },
        'Піца Папероні': {
            'price': 140,
            'photo': 'photos/pizza_pepperoni.jpg'
        },
        'Картопля фрі': {
            'price': 45,
            'photo': 'photos/french_fries.jpeg'
        },
        'Картопля по-селянськи': {
            'price': 50,
            'photo': 'photos/country_potatoes.jpg'
        }
    },
    'Салати': {
        'Цезар': {
            'price': 80,
            'photo': 'photos/salat_cezar.png'
        },
        'Олів\'є': {
            'price': 90,
            'photo': 'photos/salat_olive.jpg'
        },
        'Салат Айзберг': {
            'price': 75,
            'photo': 'photos/salat_iceberg.jpg'
        },
        'Грецький': {
            'price': 85,
            'photo': 'photos/greek_salad.jpg'
        },
        'Вінігрет': {
            'price': 70,
            'photo': 'photos/vinigret.jpg'
        }
    },
    'Напої': {
        'Кока-Кола': {
            'price': 30,
            'photo': 'photos/photo_koka_cola.jpg'
        },
        'Фанта': {
            'price': 30,
            'photo': 'photos/photo_fanta.jpg'
        },
        'Соки': {
            'price': 40,
            'photo': 'photos/photo_soki.jpg'
        },
        'Узвар': {
            'price': 35,
            'photo': 'photos/uzvar.jpg'
        },
        'Квас': {
            'price': 30,
            'photo': 'photos/kvas.jpg'
        }
    }
}
# Modified cart logic with emojis
cart = {}
user_data = {}
reservations = {}

ADMIN_CHAT_ID = '720924968'


def main_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🍽️ Меню', '🛒 Кошик', '✏️ Залишити відгук', '🍴 Забронювати столик')
    bot.send_message(message.chat.id, 'Оберіть опцію:', reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '🔙 Назад')
def go_back(message):
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '🍽️ Меню')
def show_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🍲 Страви', '🥗 Салати', '🥤 Напої', '🔙 Назад')
    bot.send_message(message.chat.id, 'Оберіть категорію:', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['🍲 Страви', '🥗 Салати', '🥤 Напої'])
def category_menu(message):
    category = message.text[2:]  # Remove emoji to match menu keys
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

    items = menu[category]
    for item in items:
        markup.add(item)
    markup.add('🔙 Назад')

    for item, details in items.items():
        price = details['price']
        photo_path = details['photo']
        with open(photo_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)
            bot.send_message(message.chat.id, f'{item} - {price} грн')

    bot.send_message(message.chat.id, 'Оберіть товар:', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in menu['Страви'].keys())
def dish_menu(message):
    dish = message.text
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['item'] = dish
    bot.send_message(user_id, '📝 Введіть кількість:')
    bot.register_next_step_handler(message, process_quantity)


@bot.message_handler(func=lambda message: message.text in menu['Салати'].keys())
def salad_menu(message):
    salad = message.text
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['item'] = salad
    bot.send_message(user_id, '📝 Введіть кількість:')
    bot.register_next_step_handler(message, process_quantity)


@bot.message_handler(func=lambda message: message.text in menu['Напої'].keys())
def drink_menu(message):
    drink = message.text
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['item'] = drink
    bot.send_message(user_id, '📝 Введіть кількість:')
    bot.register_next_step_handler(message, process_quantity)


def process_quantity(message):
    user_id = message.chat.id
    if user_id not in user_data or 'item' not in user_data[user_id]:
        return

    item = user_data[user_id]['item']

    if item in menu['Страви'].keys():
        category = 'Страви'
    elif item in menu['Салати'].keys():
        category = 'Салати'
    elif item in menu['Напої'].keys():
        category = 'Напої'
    else:
        return

    dish = item
    price = menu[category][dish]['price']

    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, '❗ Введіть дійсне додатне число для кількості.')
        return

    total_price = price * quantity

    if user_id not in cart:
        cart[user_id] = {}
    if category not in cart[user_id]:
        cart[user_id][category] = {}

    cart[user_id][category][dish] = {
        'price': price,
        'quantity': quantity,
        'total_price': total_price
    }

    bot.send_message(user_id, f'✅ Додано {quantity} шт. {dish} в кошик.\n💰 Вартість: {total_price} грн.')
    bot.clear_step_handler_by_chat_id(user_id)
    show_menu(message)


@bot.message_handler(func=lambda message: message.text == '🛒 Кошик')
def view_cart(message):
    user_id = message.chat.id
    if user_id not in cart or not cart[user_id]:
        bot.send_message(user_id, '🛒 Ваш кошик порожній.')
        return

    text = '🛒 *Ваше замовлення:*\n'
    total = 0
    for category, items in cart[user_id].items():
        text += f'\n📂 *{category}*\n'
        for item, info in items.items():
            text += f'  - _{item}_: {info["quantity"]} шт. × {info["price"]} грн = {info["total_price"]} грн\n'
            total += info['total_price']

    text += f'\n💳 *Загалом:* {total} грн\n\n'

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('✅ Оформити замовлення', '❌ Очистити кошик', '🔙 Назад')

    bot.send_message(user_id, text, parse_mode='Markdown', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '❌ Очистити кошик')
def clear_cart(message):
    user_id = message.chat.id
    if user_id in cart:
        cart[user_id] = {}
    bot.send_message(user_id, '🧹 Кошик очищено.')
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '✅ Оформити замовлення')
def place_order(message):
    user_id = message.chat.id
    if user_id not in cart or not cart[user_id]:
        bot.send_message(user_id, '🛒 Ваш кошик порожній.')
        return

    bot.send_message(user_id, 'Будь ласка, введіть своє ім\'я:')
    bot.register_next_step_handler(message, process_name)


def process_name(message):
    user_id = message.chat.id
    name = message.text
    user_data[user_id]['name'] = name

    bot.send_message(user_id, 'Будь ласка, введіть адресу доставки:')
    bot.register_next_step_handler(message, process_address)


def process_address(message):
    user_id = message.chat.id
    address = message.text
    user_data[user_id]['address'] = address

    bot.send_message(user_id, 'Будь ласка, введіть номер телефону:')
    bot.register_next_step_handler(message, process_phone)


def process_phone(message):
    user_id = message.chat.id
    phone = message.text

    if not re.match(r'^\d{1,12}$', phone):
        bot.send_message(user_id, '❗ Невірний формат номера телефону. Введіть тільки цифри, не більше 12 символів.')
        bot.send_message(user_id, 'Будь ласка, введіть номер телефону ще раз:')
        bot.register_next_step_handler(message, process_phone)
        return

    user_data[user_id]['phone'] = phone

    order_details = '✅ *Ваше замовлення:*\n'
    total_price = 0

    for category, items in cart[user_id].items():
        order_details += f'\n📂 *{category}*\n'
        for item, details in items.items():
            # Екрануємо символи, які можуть порушити Markdown форматування
            safe_item = item.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
            order_details += f'  - {safe_item}: {details["quantity"]} шт. × {details["price"]} грн = {details["total_price"]} грн\n'
            total_price += details['total_price']

    order_details += f'\n💳 *Загальна сума:* {total_price} грн\n\n'
    order_details += f'👤 *Ім\'я:* {user_data[user_id]["name"]}\n'
    order_details += f'🏠 *Адреса доставки:* {user_data[user_id]["address"]}\n'
    order_details += f'📱 *Номер телефону:* {user_data[user_id]["phone"][:3]}***'

    try:
        bot.send_message(user_id, order_details, parse_mode='Markdown')
    except Exception as e:
        # Якщо виникла помилка з Markdown, відправляємо без форматування
        bot.send_message(user_id, order_details.replace('*', '').replace('_', ''))

    bot.send_message(user_id, 'Дякуємо за ваше замовлення! Ми зв\'яжемося з вами найближчим часом')

    admin_order_details = '🆕 *Нове замовлення:*\n'
    admin_order_details += f'🆔 *ID користувача:* {user_id}\n'
    admin_order_details += order_details.replace(f'📱 *Номер телефону:* {user_data[user_id]["phone"][:3]}***',
                                                 f'📱 *Номер телефону:* {user_data[user_id]["phone"]}')

    try:
        bot.send_message(ADMIN_CHAT_ID, admin_order_details, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(ADMIN_CHAT_ID, admin_order_details.replace('*', '').replace('_', ''))

    if user_id in cart:
        cart[user_id] = {}
    if user_id in user_data:
        user_data.pop(user_id, None)
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '✏️ Залишити відгук')
def leave_feedback(message):
    user_id = message.chat.id
    bot.send_message(user_id, 'Напишіть, будь ласка, відгук про наш сервіс, щоб ми могли вдосконалюватись!')
    bot.register_next_step_handler(message, process_feedback)


def process_feedback(message):
    user_id = message.chat.id
    feedback = message.text
    bot.send_message(user_id, 'Дякуємо за відгук! Ваша думка важлива для нас!')
    bot.send_message(ADMIN_CHAT_ID, f'📝 Відгук від користувача {user_id}:\n{feedback}')
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '🍴 Забронювати столик')
def book_table(message):
    user_id = message.chat.id
    bot.send_message(user_id, 'Введіть кількість осіб:')
    bot.register_next_step_handler(message, process_guests_number)


def process_guests_number(message):
    user_id = message.chat.id
    try:
        guests = int(message.text)
        if guests <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, '❗ Будь ласка, введіть коректне число (більше 0)')
        bot.register_next_step_handler(message, process_guests_number)
        return

    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['guests'] = guests

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    today = datetime.now().date()
    dates = []
    for i in range(7):
        date = today + timedelta(days=i)
        dates.append(date.strftime('%d.%m.%Y'))
    markup.add(*dates)
    markup.add('🔙 Назад')

    bot.send_message(user_id, 'Оберіть дату бронювання:', reply_markup=markup)
    bot.register_next_step_handler(message, process_booking_date)


def process_booking_date(message):
    user_id = message.chat.id
    date_str = message.text

    if date_str == '🔙 Назад':
        main_menu(message)
        return

    try:
        booking_date = datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        bot.send_message(user_id, '❗ Будь ласка, оберіть дату з запропонованих варіантів')
        bot.register_next_step_handler(message, process_booking_date)
        return

    if booking_date < datetime.now().date():
        bot.send_message(user_id, '❗ Не можна бронювати столик на минулі дати')
        bot.register_next_step_handler(message, process_booking_date)
        return

    user_data[user_id]['booking_date'] = date_str

    markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    times = ['10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00']
    markup.add(*times)
    markup.add('🔙 Назад')

    bot.send_message(user_id, 'Оберіть час бронювання:', reply_markup=markup)
    bot.register_next_step_handler(message, process_booking_time)


def process_booking_time(message):
    user_id = message.chat.id
    time_str = message.text

    if time_str == '🔙 Назад':
        main_menu(message)
        return

    if time_str not in ['10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00']:
        bot.send_message(user_id, '❗ Будь ласка, оберіть час з запропонованих варіантів')
        bot.register_next_step_handler(message, process_booking_time)
        return

    user_data[user_id]['booking_time'] = time_str
    bot.send_message(user_id, 'Введіть ваше ім\'я для бронювання:')
    bot.register_next_step_handler(message, process_booking_name)


def process_booking_name(message):
    user_id = message.chat.id
    name = message.text
    user_data[user_id]['booking_name'] = name
    bot.send_message(user_id, 'Введіть ваш номер телефону для підтвердження бронювання:')
    bot.register_next_step_handler(message, process_booking_phone)


def process_booking_phone(message):
    user_id = message.chat.id
    phone = message.text

    if not re.match(r'^\d{1,12}$', phone):
        bot.send_message(user_id, '❗ Невірний формат номера телефону. Введіть тільки цифри, не більше 12 символів.')
        bot.send_message(user_id, 'Будь ласка, введіть номер телефону ще раз:')
        bot.register_next_step_handler(message, process_booking_phone)
        return

    user_data[user_id]['booking_phone'] = phone

    guests = user_data[user_id]['guests']
    date = user_data[user_id]['booking_date']
    time = user_data[user_id]['booking_time']
    name = user_data[user_id]['booking_name']

    # Екрануємо спеціальні символи Markdown
    safe_name = name.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
    safe_date = date.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
    safe_time = time.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')

    user_reservation_details = (
        f"✅ *Ваше бронювання:*\n"
        f"👤 *Ім'я:* {safe_name}\n"
        f"📱 *Телефон:* {phone[:3]}***\n"
        f"📅 *Дата:* {safe_date}\n"
        f"⏰ *Час:* {safe_time}\n"
        f"👥 *Кількість осіб:* {guests}"
    )

    try:
        bot.send_message(user_id, user_reservation_details, parse_mode='Markdown')
    except Exception as e:
        # Якщо виникла помилка, відправляємо без форматування
        plain_text = user_reservation_details.replace('*', '').replace('_', '')
        bot.send_message(user_id, plain_text)

    bot.send_message(user_id, 'Ваш столик успішно заброньовано! Очікуємо вас у зазначений час.')

    admin_reservation_details = (
        f"🆕 *Нове бронювання столика:*\n"
        f"🆔 *ID користувача:* {user_id}\n"
        f"👤 *Ім'я:* {safe_name}\n"
        f"📱 *Телефон:* {phone}\n"
        f"📅 *Дата:* {safe_date}\n"
        f"⏰ *Час:* {safe_time}\n"
        f"👥 *Кількість осіб:* {guests}"
    )

    try:
        bot.send_message(ADMIN_CHAT_ID, admin_reservation_details, parse_mode='Markdown')
    except Exception as e:
        plain_text = admin_reservation_details.replace('*', '').replace('_', '')
        bot.send_message(ADMIN_CHAT_ID, plain_text)

    if user_id not in reservations:
        reservations[user_id] = []
    reservations[user_id].append({
        'name': name,
        'phone': phone,
        'date': date,
        'time': time,
        'guests': guests
    })

    main_menu(message)


if __name__ == '__main__':
    bot.polling()