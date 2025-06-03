import telebot
from telebot import types
import re
from datetime import datetime, timedelta
import telebot.apihelper

# Ініціалізація бота з токеном
bot = telebot.TeleBot('API-ТОКЕН')

# Меню ресторану з цінами та шляхами до фото
menu = {
    'Страви': {
        'Вареники': {'price': 50, 'photo': 'photos/varenyk.jpg'},
        'Деруни': {'price': 70, 'photo': 'photos/deruny.jpg'},
        'Борщ': {'price': 60, 'photo': 'photos/borshch.jpg'},
        'Солянка': {'price': 65, 'photo': 'photos/solyanka.jpg'},
        'Холодник': {'price': 55, 'photo': 'photos/holodnik.jpg'},
        'Піца Маргарита': {'price': 120, 'photo': 'photos/pizza_margarita.jpg'},
        'Піца 4 Сири': {'price': 150, 'photo': 'photos/pizza_4cheese.jpg'},
        'Піца Папероні': {'price': 140, 'photo': 'photos/pizza_pepperoni.jpg'},
        'Картопля фрі': {'price': 45, 'photo': 'photos/french_fries.jpeg'},
        'Картопля по-селянськи': {'price': 50, 'photo': 'photos/country_potatoes.jpg'}
    },
    'Салати': {
        'Цезар': {'price': 80, 'photo': 'photos/salat_cezar.png'},
        'Олів\'є': {'price': 90, 'photo': 'photos/salat_olive.jpg'},
        'Салат Айзберг': {'price': 75, 'photo': 'photos/salat_iceberg.jpg'},
        'Грецький': {'price': 85, 'photo': 'photos/greek_salad.jpg'},
        'Вінігрет': {'price': 70, 'photo': 'photos/vinigret.jpg'}
    },
    'Напої': {
        'Кока-Кола': {'price': 30, 'photo': 'photos/photo_koka_cola.jpg'},
        'Фанта': {'price': 30, 'photo': 'photos/photo_fanta.jpg'},
        'Соки': {'price': 40, 'photo': 'photos/photo_soki.jpg'},
        'Узвар': {'price': 35, 'photo': 'photos/uzvar.jpg'},
        'Квас': {'price': 30, 'photo': 'photos/kvas.jpg'}
    }
}

# Глобальні змінні для зберігання даних
cart = {}  # Кошик користувачів
user_data = {}  # Тимчасові дані користувачів
reservations = {}  # Бронювання столиків

ADMIN_CHAT_ID = '720924968'  # ID адміністратора для сповіщень


def main_menu(message):
    """Показує головне меню з основними опціями"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = ['🍽️ Меню', '🛒 Кошик', '✏️ Залишити відгук', '🍴 Забронювати столик']
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Оберіть опцію:', reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    """Обробник команди /start"""
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '🔙 Назад')
def go_back(message):
    """Обробник кнопки 'Назад'"""
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '🍽️ Меню')
def show_menu(message):
    """Показує меню категорій"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = ['🍲 Страви', '🥗 Салати', '🥤 Напої', '🔙 Назад']
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Оберіть категорію:', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['🍲 Страви', '🥗 Салати', '🥤 Напої'])
def category_menu(message):
    """Показує товари у вибраній категорії"""
    category = message.text[2:]
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

    items = menu[category]
    for item in items:
        markup.add(item)
    markup.add('🔙 Назад')

    for item, details in items.items():
        try:
            with open(details['photo'], 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
        except FileNotFoundError:
            bot.send_message(message.chat.id, f"🖼️ Фото для {item} тимчасово відсутнє")

        bot.send_message(message.chat.id, f'{item} - {details["price"]} грн')

    bot.send_message(message.chat.id, 'Оберіть товар:', reply_markup=markup)


# Обробники вибору страв/салатів/напоїв
@bot.message_handler(func=lambda message: message.text in menu['Страви'].keys())
def dish_menu(message):
    """Обробляє вибір страви"""
    handle_product_selection(message)


@bot.message_handler(func=lambda message: message.text in menu['Салати'].keys())
def salad_menu(message):
    """Обробляє вибір салату"""
    handle_product_selection(message)


@bot.message_handler(func=lambda message: message.text in menu['Напої'].keys())
def drink_menu(message):
    """Обробляє вибір напою"""
    handle_product_selection(message)


def handle_product_selection(message):
    """Спільна функція для обробки вибору товару"""
    product = message.text
    user_id = message.chat.id
    user_data[user_id] = {'item': product}
    bot.send_message(user_id, '📝 Введіть кількість:')
    bot.register_next_step_handler(message, process_quantity)


def process_quantity(message):
    """Обробляє кількість товару та додає до кошика"""
    user_id = message.chat.id
    if user_id not in user_data or 'item' not in user_data[user_id]:
        return

    item = user_data[user_id]['item']

    # Визначаємо категорію товару
    for category in menu:
        if item in menu[category]:
            price = menu[category][item]['price']
            try:
                quantity = int(message.text)
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                bot.send_message(user_id, '❗ Введіть коректне число більше 0')
                return

            # Додаємо товар до кошика
            if user_id not in cart:
                cart[user_id] = {}
            if category not in cart[user_id]:
                cart[user_id][category] = {}

            cart[user_id][category][item] = {
                'price': price,
                'quantity': quantity,
                'total_price': price * quantity
            }

            bot.send_message(user_id, f'✅ Додано {quantity} шт. {item} в кошик!\n💰 Вартість: {price * quantity} грн.')
            show_menu(message)
            return

    bot.send_message(user_id, '❌ Помилка при додаванні товару')


@bot.message_handler(func=lambda message: message.text == '🛒 Кошик')
def view_cart(message):
    """Показує вміст кошика"""
    user_id = message.chat.id
    if not cart.get(user_id):
        bot.send_message(user_id, '🛒 Ваш кошик порожній.')
        return

    text = '<b>🛒 Ваше замовлення:</b>\n'
    total = 0

    for category, items in cart[user_id].items():
        text += f'\n<b>📂 {category}</b>\n'
        for item, info in items.items():
            text += f'  - {item}: {info["quantity"]} шт. × {info["price"]} грн = {info["total_price"]} грн\n'
            total += info['total_price']

    text += f'\n<b>💳 Загалом:</b> {total} грн'

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('✅ Оформити замовлення', '❌ Очистити кошик', '🔙 Назад')

    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '❌ Очистити кошик')
def clear_cart(message):
    """Очищає кошик користувача"""
    user_id = message.chat.id
    cart[user_id] = {}
    bot.send_message(user_id, '🧹 Кошик очищено!')
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '✅ Оформити замовлення')
def place_order(message):
    """Починає процес оформлення замовлення"""
    user_id = message.chat.id
    if not cart.get(user_id):
        bot.send_message(user_id, '🛒 Ваш кошик порожній.')
        return

    bot.send_message(user_id, 'Будь ласка, введіть своє ім\'я:')
    bot.register_next_step_handler(message, process_name)


def process_name(message):
    """Обробляє ім'я для замовлення"""
    user_id = message.chat.id
    user_data[user_id] = {'name': message.text}
    bot.send_message(user_id, 'Введіть адресу доставки:')
    bot.register_next_step_handler(message, process_address)


def process_address(message):
    """Обробляє адресу доставки"""
    user_id = message.chat.id
    user_data[user_id]['address'] = message.text
    bot.send_message(user_id, 'Введіть номер телефону:')
    bot.register_next_step_handler(message, process_phone)


def process_phone(message):
    """Обробляє номер телефону та завершує замовлення"""
    user_id = message.chat.id
    phone = message.text

    if not re.match(r'^\d{10,12}$', phone):
        bot.send_message(user_id, '❗ Невірний формат телефону. Введіть 10-12 цифр')
        bot.register_next_step_handler(message, process_phone)
        return

    user_data[user_id]['phone'] = phone

    # Повідомлення для клієнта
    order_text = "<b>✅ Ваше замовлення прийнято!</b>\n\n"
    total = 0

    for category, items in cart[user_id].items():
        order_text += f"<b>🍽️ {category}</b>\n"
        for item, details in items.items():
            order_text += f"  - {item}: {details['quantity']} × {details['price']} грн = {details['total_price']} грн\n"
            total += details['total_price']

    order_text += f"\n<b>💰 Сума:</b> {total} грн\n"
    order_text += f"<b>👤 Ім'я:</b> {user_data[user_id]['name']}\n"
    order_text += f"<b>🏠 Адреса:</b> {user_data[user_id]['address']}\n"
    order_text += f"<b>📱 Телефон:</b> {phone[:3]}***\n\n"
    order_text += "Дякуємо за замовлення! Очікуйте дзвінка."

    # Відправляємо користувачу
    bot.send_message(user_id, order_text, parse_mode='HTML')

    # Повідомлення для адміністратора
    admin_text = "<b>🆕 Нове замовлення</b>\n\n"
    for category, items in cart[user_id].items():
        admin_text += f"<b>🍽️ {category}</b>\n"
        for item, details in items.items():
            admin_text += f"  - {item}: {details['quantity']} × {details['price']} грн = {details['total_price']} грн\n"

    admin_text += f"\n<b>💰 Сума:</b> {total} грн\n"
    admin_text += f"<b>👤 Ім'я:</b> {user_data[user_id]['name']}\n"
    admin_text += f"<b>🏠 Адреса:</b> {user_data[user_id]['address']}\n"
    admin_text += f"<b>📱 Телефон:</b> {phone}"

    bot.send_message(ADMIN_CHAT_ID, admin_text, parse_mode='HTML')

    # Очищаємо дані
    cart.pop(user_id, None)
    user_data.pop(user_id, None)
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '✏️ Залишити відгук')
def leave_feedback(message):
    """Запитує відгук від користувача"""
    bot.send_message(message.chat.id, '📝 Напишіть ваш відгук про наш сервіс:')
    bot.register_next_step_handler(message, process_feedback)


def process_feedback(message):
    """Обробляє відгук та надсилає адміністратору"""
    feedback = message.text
    bot.send_message(message.chat.id, '❤️ Дякуємо за ваш відгук!')
    bot.send_message(ADMIN_CHAT_ID,
                     f"📝 Відгук від @{message.from_user.username or message.from_user.first_name}:\n{feedback}")
    main_menu(message)


@bot.message_handler(func=lambda message: message.text == '🍴 Забронювати столик')
def book_table(message):
    """Починає процес бронювання столика"""
    bot.send_message(message.chat.id, '👥 На скільки осіб бронюєте столик?')
    bot.register_next_step_handler(message, process_guests)


def process_guests(message):
    """Обробляє кількість гостей"""
    try:
        guests = int(message.text)
        if guests < 1 or guests > 20:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, '❗ Введіть число від 1 до 20')
        bot.register_next_step_handler(message, process_guests)
        return

    user_id = message.chat.id
    user_data[user_id] = {'guests': guests}

    # Генеруємо доступні дати (наступні 7 днів)
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    dates = [(datetime.now() + timedelta(days=i)).strftime('%d.%m.%Y') for i in range(7)]
    markup.add(*dates)
    markup.add('🔙 Назад')

    bot.send_message(user_id, '📅 Оберіть дату:', reply_markup=markup)
    bot.register_next_step_handler(message, process_date)


def process_date(message):
    """Обробляє вибір дати"""
    if message.text == '🔙 Назад':
        main_menu(message)
        return

    try:
        datetime.strptime(message.text, '%d.%m.%Y')
    except ValueError:
        bot.send_message(message.chat.id, '❗ Оберіть дату зі списку')
        bot.register_next_step_handler(message, process_date)
        return

    user_id = message.chat.id
    user_data[user_id]['date'] = message.text

    # Пропонуємо вибрати час
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    times = ['10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00']
    markup.add(*times)
    markup.add('🔙 Назад')

    bot.send_message(user_id, '⏰ Оберіть час:', reply_markup=markup)
    bot.register_next_step_handler(message, process_time)


def process_time(message):
    """Обробляє вибір часу"""
    if message.text == '🔙 Назад':
        main_menu(message)
        return

    if message.text not in ['10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00']:
        bot.send_message(message.chat.id, '❗ Оберіть час зі списку')
        bot.register_next_step_handler(message, process_time)
        return

    user_id = message.chat.id
    user_data[user_id]['time'] = message.text

    bot.send_message(user_id, '👤 Введіть ваше ім\'я для бронювання:')
    bot.register_next_step_handler(message, process_booking_name)


def process_booking_name(message):
    """Обробляє ім'я для бронювання"""
    user_id = message.chat.id
    user_data[user_id]['name'] = message.text
    bot.send_message(user_id, '📱 Введіть ваш номер телефону:')
    bot.register_next_step_handler(message, process_booking_phone)


def process_booking_phone(message):
    """Завершує бронювання"""
    phone = message.text
    if not re.match(r'^\d{10,12}$', phone):
        bot.send_message(message.chat.id, '❗ Введіть коректний номер телефону (10-12 цифр)')
        bot.register_next_step_handler(message, process_booking_phone)
        return

    user_id = message.chat.id
    user_data[user_id]['phone'] = phone

    # Повідомлення для клієнта
    reservation_info = (
        "<b>✅ Ваше бронювання прийнято!</b>\n\n"
        f"<b>👤 Ім'я:</b> {user_data[user_id]['name']}\n"
        f"<b>📱 Телефон:</b> {phone[:3]}***\n"
        f"<b>👥 Гості:</b> {user_data[user_id]['guests']}\n"
        f"<b>📅 Дата:</b> {user_data[user_id]['date']}\n"
        f"<b>⏰ Час:</b> {user_data[user_id]['time']}\n\n"
        "Дякуємо за бронювання! Чекаємо на вас!"
    )

    # Відправляємо користувачу
    bot.send_message(user_id, reservation_info, parse_mode='HTML')

    # Повідомлення для адміністратора
    admin_info = (
        "<b>🆕 Нове бронювання</b>\n\n"
        f"<b>👤 Ім'я:</b> {user_data[user_id]['name']}\n"
        f"<b>📱 Телефон:</b> {phone}\n"
        f"<b>👥 Гості:</b> {user_data[user_id]['guests']}\n"
        f"<b>📅 Дата:</b> {user_data[user_id]['date']}\n"
        f"<b>⏰ Час:</b> {user_data[user_id]['time']}"
    )

    bot.send_message(ADMIN_CHAT_ID, admin_info, parse_mode='HTML')

    # Зберігаємо бронювання
    if user_id not in reservations:
        reservations[user_id] = []
    reservations[user_id].append(user_data[user_id].copy())

    # Очищаємо тимчасові дані
    user_data.pop(user_id, None)
    main_menu(message)


if __name__ == '__main__':
    # Видаляємо вебхук перед запуском (якщо він був)
    telebot.apihelper.delete_webhook(bot.token)

    # Запускаємо бота
    print("Бот запущений...")
    bot.polling(none_stop=True)
