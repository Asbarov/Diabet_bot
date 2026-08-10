from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import db
from config import ADMIN_IDS

from keyboards.keyboards import (
    get_role_keyboard,
    get_patient_menu_keyboard,
    get_doctor_menu_keyboard,
    get_doctor_patient_menu_keyboard,
    get_admin_only_keyboard,
)


router = Router(name="start")


DOCTOR_STATUS_TEXT = {
    "pending": (
        "⏳ Ваша заявка врача ещё находится "
        "на рассмотрении у администратора."
    ),
    "approved": (
        "✅ Вы зарегистрированы как врач "
        "и подтверждены администратором."
    ),
    "rejected": (
        "❌ Ваша заявка врача была отклонена."
    ),
}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


NO_USERNAME_TEXT = (
    "⚠️ Для регистрации нужен публичный <b>username</b> в Telegram — "
    "по нему врачи и пациенты смогут перейти в чат с вами напрямую.\n\n"
    "Как настроить:\n"
    "1. Откройте Настройки → Имя пользователя в приложении Telegram.\n"
    "2. Придумайте и сохраните username.\n"
    "3. Вернитесь в этот чат и отправьте /start ещё раз."
)


def build_main_keyboard(
    patient,
    doctor,
    admin: bool,
):

    # Пациент + подтверждённый врач
    if patient and doctor and doctor["status"] == "approved":
        return get_doctor_patient_menu_keyboard(
            is_admin=admin
        )

    # Только пациент
    if patient:
        return get_patient_menu_keyboard(
            is_admin=admin
        )

    # Подтверждённый врач
    if doctor and doctor["status"] == "approved":
        return get_doctor_menu_keyboard(
            is_admin=admin
        )

    # Только администратор
    if admin:
        return get_admin_only_keyboard()

    return None


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    user_id = message.from_user.id

    admin = is_admin(user_id)

    patient = await db.get_patient(user_id)
    doctor = await db.get_doctor(user_id)

    # --------------------------------------------------------
    # Новый пользователь
    # --------------------------------------------------------

    if not patient and not doctor:

        await message.answer(
            "Добро пожаловать! 👋\n\n"
            "Выберите вашу роль:",
            reply_markup=get_role_keyboard(
                is_admin=admin
            ),
        )

        return

    # --------------------------------------------------------
    # Уже зарегистрированный пользователь
    # --------------------------------------------------------

    parts = [
        "С возвращением! 👋"
    ]

    if patient:
        parts.append(
            f"👤 Вы зарегистрированы как пациент: "
            f"<b>{patient['full_name']}</b>"
        )

    if doctor:

        status = doctor["status"]

        status_text = DOCTOR_STATUS_TEXT.get(
            status,
            "",
        )

        parts.append(
            f"👨‍⚕️ Врач: "
            f"<b>{doctor['full_name']}</b>\n"
            f"{status_text}"
        )

    if admin:
        parts.append(
            "🔧 У вас есть права администратора."
        )

    keyboard = build_main_keyboard(
        patient=patient,
        doctor=doctor,
        admin=admin,
    )

    await message.answer(
        "\n\n".join(parts),
        reply_markup=keyboard,
    )


# ============================================================
# ВЫБОР РОЛИ — ПАЦИЕНТ
# ============================================================

@router.message(F.text == "🧑 Я пациент")
async def choose_patient_role(
    message: Message,
    state: FSMContext,
):
    from states.states import PatientRegistration

    if not message.from_user.username:
        await message.answer(NO_USERNAME_TEXT)
        return

    await state.set_state(
        PatientRegistration.full_name
    )

    await message.answer(
        "Отлично! Начнём регистрацию пациента.\n\n"
        "Как вас зовут?",
    )


# ============================================================
# ВЫБОР РОЛИ — ВРАЧ
# ============================================================

@router.message(F.text == "👨‍⚕️ Я врач")
async def choose_doctor_role(
    message: Message,
    state: FSMContext,
):
    from states.states import DoctorRegistration

    if not message.from_user.username:
        await message.answer(NO_USERNAME_TEXT)
        return

    await state.set_state(
        DoctorRegistration.full_name
    )

    await message.answer(
        "Регистрация врача.\n\n"
        "Введите ваше ФИО:",
    )