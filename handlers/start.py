from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import db
from config import ADMIN_IDS
from keyboards.keyboards import (
    get_role_keyboard,
    get_patient_menu_keyboard,
    get_admin_only_keyboard,
)

router = Router(name="start")

DOCTOR_STATUS_TEXT = {
    "pending": "⏳ Ваша заявка врача ещё на рассмотрении у администратора.",
    "approved": "✅ Вы зарегистрированы как врач и подтверждены администратором.",
    "rejected": "❌ Ваша заявка врача была отклонена администратором.",
}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    # Роли независимы друг от друга: пользователь может одновременно быть
    # и пациентом, и врачом (в БД это две отдельные записи по одному и тому
    # же Telegram ID), а ADMIN_IDS — это отдельная, дополнительная привилегия
    # поверх любой из ролей, а не замена им.
    admin = is_admin(message.from_user.id)
    patient = await db.get_patient(message.from_user.id)
    doctor = await db.get_doctor(message.from_user.id)

    # Совсем новый пользователь — ни пациент, ни врач. Даже если он админ,
    # ему всё равно предлагаем выбрать роль (плюс кнопка админки рядом).
    if not patient and not doctor:
        await message.answer(
            "Добро пожаловать в бота для пациентов с сахарным диабетом и "
            "врачей-эндокринологов! 👋\n\n"
            "Пожалуйста, выберите, кто вы:",
            reply_markup=get_role_keyboard(is_admin=admin),
        )
        return

    # Дальше собираем приветствие из всех применимых блоков сразу.
    parts = ["С возвращением! 👋"]

    if patient:
        parts.append(f"👤 Вы зарегистрированы как пациент: {patient['full_name']}.")

    if doctor:
        status_text = DOCTOR_STATUS_TEXT.get(doctor["status"], "")
        parts.append(f"👨‍⚕️ Врач {doctor['full_name']}.\n{status_text}")

    if admin:
        parts.append(
            "🔧 У вас есть права администратора.\n"
            "Команды: /admin — заявки врачей, /doctors — все врачи в базе."
        )

    # Клавиатура: если есть карта пациента — показываем его меню (с кнопкой
    # админки, если применимо). Если пациента нет, но есть права админа —
    # хотя бы кнопка админки. Иначе — без клавиатуры (как и раньше для
    # "чистого" врача без прав администратора).
    if patient:
        keyboard = get_patient_menu_keyboard(is_admin=admin)
    elif admin:
        keyboard = get_admin_only_keyboard()
    else:
        keyboard = None

    await message.answer("\n\n".join(parts), reply_markup=keyboard)


@router.message(F.text == "🧑 Я пациент")
async def choose_patient_role(message: Message, state: FSMContext):
    from states.states import PatientRegistration
    from keyboards.keyboards import remove_keyboard

    await state.set_state(PatientRegistration.full_name)
    await message.answer(
        "Отлично! Начнём регистрацию карты пациента.\n\n"
        "Как вас зовут? (введите ФИО или имя)",
        reply_markup=remove_keyboard,
    )


@router.message(F.text == "👨‍⚕️ Я врач")
async def choose_doctor_role(message: Message, state: FSMContext):
    from states.states import DoctorRegistration
    from keyboards.keyboards import remove_keyboard

    await state.set_state(DoctorRegistration.full_name)
    await message.answer(
        "Регистрация врача-эндокринолога.\n\n"
        "Введите ваше ФИО:",
        reply_markup=remove_keyboard,
    )
