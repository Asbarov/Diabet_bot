from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

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


CONSENT_TEXT = (
    "📋 <b>Согласие на обработку персональных данных</b>\n\n"
    "Для регистрации в боте нужно собрать ваши персональные данные: "
    "имя, возраст, город, телефон, username{extra}.\n\n"
    "Эти данные используются только для работы бота — чтобы врач и "
    "пациент могли найти друг друга и связаться — и никому не "
    "передаются.\n\n"
    "Удалить свои данные из бота можно в любой момент командой "
    "/delete_me.\n\n"
    "Нажимая «Согласен», вы подтверждаете согласие на обработку "
    "перечисленных данных."
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
    if not message.from_user.username:
        await message.answer(NO_USERNAME_TEXT)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Согласен, продолжить", callback_data="consent:patient")
    builder.button(text="❌ Отмена", callback_data="consent:cancel")
    builder.adjust(1)

    await message.answer(
        CONSENT_TEXT.format(
            extra=", сведения о диабете (стаж, терапия), рост и вес"
        ),
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "consent:patient")
async def consent_patient(
    callback: CallbackQuery,
    state: FSMContext,
):
    from states.states import PatientRegistration

    await state.set_state(PatientRegistration.full_name)

    await callback.message.edit_text(
        callback.message.html_text + "\n\n✅ <b>Согласие получено.</b>",
        reply_markup=None,
    )
    await callback.answer()

    await callback.message.answer(
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
    if not message.from_user.username:
        await message.answer(NO_USERNAME_TEXT)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Согласен, продолжить", callback_data="consent:doctor")
    builder.button(text="❌ Отмена", callback_data="consent:cancel")
    builder.adjust(1)

    await message.answer(
        CONSENT_TEXT.format(
            extra=", место работы, специальность и стаж"
        ),
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "consent:doctor")
async def consent_doctor(
    callback: CallbackQuery,
    state: FSMContext,
):
    from states.states import DoctorRegistration

    await state.set_state(DoctorRegistration.full_name)

    await callback.message.edit_text(
        callback.message.html_text + "\n\n✅ <b>Согласие получено.</b>",
        reply_markup=None,
    )
    await callback.answer()

    await callback.message.answer(
        "Регистрация врача.\n\n"
        "Введите ваше ФИО:",
    )


@router.callback_query(F.data == "consent:cancel")
async def consent_cancel(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        callback.message.html_text + "\n\n❌ <b>Регистрация отменена.</b>",
        reply_markup=None,
    )
    await callback.answer()


# ============================================================
# УДАЛЕНИЕ СВОИХ ДАННЫХ
# ============================================================

@router.message(Command("delete_me"))
async def delete_me_command(
    message: Message,
    state: FSMContext,
):
    user_id = message.from_user.id

    patient = await db.get_patient(user_id)
    doctor = await db.get_doctor(user_id)

    if not patient and not doctor:
        await message.answer(
            "У вас нет сохранённых данных в боте — удалять нечего."
        )
        return

    what = []
    if patient:
        what.append("карту пациента")
    if doctor:
        what.append("карту врача")

    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Да, удалить всё", callback_data="delete_me:confirm")
    builder.button(text="Отмена", callback_data="delete_me:cancel")
    builder.adjust(1)

    await message.answer(
        f"⚠️ Это удалит вашу {' и '.join(what)} без возможности "
        "восстановления. Придётся регистрироваться заново, если "
        "захотите вернуться.\n\nВы уверены?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "delete_me:confirm")
async def delete_me_confirm(
    callback: CallbackQuery,
    state: FSMContext,
):
    user_id = callback.from_user.id

    if await db.get_patient(user_id):
        await db.delete_patient(user_id)

    if await db.get_doctor(user_id):
        await db.delete_doctor(user_id)

    await state.clear()

    await callback.message.edit_text(
        "✅ Ваши данные удалены из бота.\n\n"
        "Если захотите вернуться — отправьте /start.",
        reply_markup=None,
    )
    await callback.answer("Данные удалены")


@router.callback_query(F.data == "delete_me:cancel")
async def delete_me_cancel(callback: CallbackQuery):
    await callback.message.edit_text(
        "Отменено. Ваши данные не тронуты.",
        reply_markup=None,
    )
    await callback.answer()