from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

ADMIN_BUTTON = KeyboardButton(text="🔧 Админ панель")


# --- Выбор роли при первом запуске ---
def get_role_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Клавиатура выбора роли. Кнопка администратора добавляется отдельной
    строкой для тех, чей Telegram ID есть в ADMIN_IDS — независимо от
    того, зарегистрированы ли они ещё как пациент или врач.
    """
    keyboard = [
        [KeyboardButton(text="🧑 Я пациент")],
        [KeyboardButton(text="👨‍⚕️ Я врач")],
    ]
    if is_admin:
        keyboard.append([ADMIN_BUTTON])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# Оставлена для обратной совместимости, если где-то использовалась напрямую.
role_keyboard = get_role_keyboard(is_admin=False)

# --- Пол пациента ---
gender_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# --- Запрос номера телефона (кнопка "поделиться контактом") ---
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# --- Главное меню пациента (заглушка — логика "Школа диабета" и
#     "Связь с врачом" будет реализована на следующем шаге) ---
def get_patient_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Меню пациента. Кнопка админки добавляется дополнительно, если у
    пациента также есть права администратора — роли не взаимоисключают
    друг друга.
    """
    keyboard = [
        [KeyboardButton(text="📚 Школа диабета")],
        [KeyboardButton(text="👨‍⚕️ Связь с врачом")],
    ]
    if is_admin:
        keyboard.append([ADMIN_BUTTON])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# Оставлена для обратной совместимости.
patient_menu_keyboard = get_patient_menu_keyboard(is_admin=False)


# --- Клавиатура для админа, у которого нет ни карты пациента, ни
#     подтверждённого статуса врача с собственным меню (пока такого меню
#     у врачей нет вообще — см. handlers/start.py) ---
def get_admin_only_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[ADMIN_BUTTON]], resize_keyboard=True)


remove_keyboard = ReplyKeyboardRemove()
