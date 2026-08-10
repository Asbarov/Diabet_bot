from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)


ADMIN_BUTTON_TEXT = "🔧 Админ панель"


def get_role_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Клавиатура выбора роли при первом запуске.
    Админская кнопка показывается дополнительно,
    если Telegram ID пользователя есть в ADMIN_IDS.
    """

    keyboard = [
        [KeyboardButton(text="🧑 Я пациент")],
        [KeyboardButton(text="👨‍⚕️ Я врач")],
    ]

    if is_admin:
        keyboard.append(
            [KeyboardButton(text=ADMIN_BUTTON_TEXT)]
        )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


# Для обратной совместимости
role_keyboard = get_role_keyboard(False)


# ---------------------------------------------------------------------------
# Пациент
# ---------------------------------------------------------------------------

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


phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📱 Отправить номер телефона",
                request_contact=True,
            )
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def get_patient_menu_keyboard(
    is_admin: bool = False,
) -> ReplyKeyboardMarkup:
    """
    Главное меню пациента.

    Если пользователь одновременно администратор,
    кнопка админ-панели добавляется в это же меню.
    """

    keyboard = [
        [KeyboardButton(text="📚 Школа диабета")],
        [KeyboardButton(text="👨‍⚕️ Связь с врачом")],
    ]

    if is_admin:
        keyboard.append(
            [KeyboardButton(text=ADMIN_BUTTON_TEXT)]
        )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

def get_doctor_menu_keyboard(
    is_admin: bool = False,
) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="👥 Список пациентов")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text=ADMIN_BUTTON_TEXT)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
def get_doctor_patient_menu_keyboard(
    is_admin: bool = False,
) -> ReplyKeyboardMarkup:

    keyboard = [
        [KeyboardButton(text="📚 Школа диабета")],
        [KeyboardButton(text="👨‍⚕️ Связь с врачом")],
        [KeyboardButton(text="👥 Список пациентов")],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text=ADMIN_BUTTON_TEXT)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
# Для обратной совместимости
patient_menu_keyboard = get_patient_menu_keyboard(False)


# ---------------------------------------------------------------------------
# Пользователь, который пока не пациент, но является админом
# ---------------------------------------------------------------------------

def get_admin_only_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_BUTTON_TEXT)]
        ],
        resize_keyboard=True,
    )


# ---------------------------------------------------------------------------
# Админ-панель
# ---------------------------------------------------------------------------

def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Меню администратора после нажатия
    кнопки «🔧 Админ панель».
    """

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨‍⚕️ Список врачей")],
            [KeyboardButton(text="📥 Заявки врачей")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


remove_keyboard = ReplyKeyboardRemove()