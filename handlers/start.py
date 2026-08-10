from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database import db

from keyboards.keyboards import (
    get_role_keyboard,
    get_patient_menu_keyboard,
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
        "❌ Ваша предыдущая заявка врача была отклонена.\n"
        "Вы можете зарегистрироваться повторно."
    ),
}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


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

    # ------------------------------------------------------------------
    # Новый пользователь
    # ------------------------------------------------------------------

    if not patient and not doctor:
        await message.answer(
            "Добро пожаловать в бота для пациентов "
            "с сахарным диабетом и врачей-эндокринологов! 👋\n\n"
            "Пожалуйста, выберите, кто вы:",
            reply_markup=get_role_keyboard(is_admin=admin),
        )
        return

    # ------------------------------------------------------------------
    # Формируем приветствие
    # ------------------------------------------------------------------

    parts = [
        "С возвращением! 👋"
    ]

    if patient:
        parts.append(
            f"👤 Вы зарегистрированы как пациент: "
            f"<b>{patient['full_name']}</b>."
        )

    if doctor:
        status_text = DOCTOR_STATUS_TEXT.get(
            doctor["status"],
            "",
        )

        parts.append(
            f"👨‍⚕️ Вы зарегистрированы как врач: "
            f"<b>{doctor['full_name']}</b>.\n"
            f"{status_text}"
        )

    if admin:
        parts.append(
            "🔧 У вас есть права администратора."
        )

    # ------------------------------------------------------------------
    # Выбираем Reply-клавиатуру
    #
    # Важно:
    # админская кнопка добавляется независимо от роли.
    # ------------------------------------------------------------------

    if patient:
        keyboard = get_patient_menu_keyboard(
            is_admin=admin
        )

    elif admin:
        keyboard = get_admin_only_keyboard()

    else:
        keyboard = None

    await message.answer(
        "\n\n".join(parts),
        reply_markup=keyboard,
    )


# ---------------------------------------------------------------------------
# Выбор пациента
# ---------------------------------------------------------------------------

@router.message(F.text == "🧑 Я пациент")
async def choose_patient_role(
    message: Message,
    state: FSMContext,
):
    from states.states import PatientRegistration
    from keyboards.keyboards import remove_keyboard

    await state.set_state(
        PatientRegistration.full_name
    )

    await message.answer(
        "Отлично! Начнём регистрацию карты пациента.\n\n"
        "Как вас зовут? (введите ФИО или имя)",
        reply_markup=remove_keyboard,
    )


# ---------------------------------------------------------------------------
# Выбор врача
# ---------------------------------------------------------------------------

@router.message(F.text == "👨‍⚕️ Я врач")
async def choose_doctor_role(
    message: Message,
    state: FSMContext,
):
    from states.states import DoctorRegistration
    from keyboards.keyboards import remove_keyboard

    await state.set_state(
        DoctorRegistration.full_name
    )

    await message.answer(
        "Регистрация врача-эндокринолога.\n\n"
        "Введите ваше ФИО:",
        reply_markup=remove_keyboard,
    )