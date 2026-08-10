from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)


ADMIN_BUTTON = KeyboardButton(text="🔧 Админ панель")


# ============================================================
# ВЫБОР РОЛИ
# ============================================================

def get_role_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🧑 Я пациент"),
        ],
        [
            KeyboardButton(text="👨‍⚕️ Я врач"),
        ],
    ]

    if is_admin:
        keyboard.append([ADMIN_BUTTON])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


role_keyboard = get_role_keyboard()


# ============================================================
# МЕНЮ ПАЦИЕНТА
# ============================================================

def get_patient_menu_keyboard(
    is_admin: bool = False,
) -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text="📚 Школа диабета"),
        ],
        [
            KeyboardButton(text="👨‍⚕️ Связь с врачом"),
        ],
    ]

    if is_admin:
        keyboard.append([ADMIN_BUTTON])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


patient_menu_keyboard = get_patient_menu_keyboard()


# ============================================================
# МЕНЮ ВРАЧА
# ============================================================

def get_doctor_menu_keyboard(
    is_admin: bool = False,
) -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text="👥 Список пациентов"),
        ],
    ]

    if is_admin:
        keyboard.append([ADMIN_BUTTON])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


# ============================================================
# МЕНЮ ВРАЧА + ПАЦИЕНТА
# ============================================================

def get_doctor_patient_menu_keyboard(
    is_admin: bool = False,
) -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text="📚 Школа диабета"),
        ],
        [
            KeyboardButton(text="👨‍⚕️ Связь с врачом"),
        ],
        [
            KeyboardButton(text="👥 Список пациентов"),
        ],
    ]

    if is_admin:
        keyboard.append([ADMIN_BUTTON])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


# ============================================================
# ТОЛЬКО АДМИН
# ============================================================

def get_admin_only_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [ADMIN_BUTTON],
        ],
        resize_keyboard=True,
    )


# ============================================================
# ПОЛ
# ============================================================

gender_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Мужской"),
            KeyboardButton(text="Женский"),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# ============================================================
# ТЕЛЕФОН
# ============================================================

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📱 Отправить номер телефона",
                request_contact=True,
            ),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# ============================================================
# УБРАТЬ КЛАВИАТУРУ
# ============================================================

remove_keyboard = ReplyKeyboardRemove()