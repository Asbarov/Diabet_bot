from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.states import DoctorRegistration
from database import db
from keyboards.keyboards import (
    get_doctor_menu_keyboard,
    get_doctor_patient_menu_keyboard,
    remove_keyboard,
    get_admin_only_keyboard,
)

from config import ADMIN_IDS


from handlers.admin import notify_admins_new_doctor


router = Router(name="doctor")


# ============================================================
# РЕГИСТРАЦИЯ ВРАЧА
# ============================================================

@router.message(DoctorRegistration.full_name)
async def process_full_name(
    message: Message,
    state: FSMContext,
):
    name = (message.text or "").strip()

    if len(name) < 2:
        await message.answer(
            "Пожалуйста, введите корректное ФИО."
        )
        return

    await state.update_data(full_name=name)
    await state.set_state(DoctorRegistration.city)

    await message.answer(
        "В каком городе вы работаете?"
    )


@router.message(DoctorRegistration.city)
async def process_city(
    message: Message,
    state: FSMContext,
):
    city = (message.text or "").strip()

    if len(city) < 2:
        await message.answer(
            "Пожалуйста, укажите город."
        )
        return

    await state.update_data(city=city)
    await state.set_state(DoctorRegistration.workplace)

    await message.answer(
        "Укажите место работы:"
    )


@router.message(DoctorRegistration.workplace)
async def process_workplace(
    message: Message,
    state: FSMContext,
):
    workplace = (message.text or "").strip()

    if not workplace:
        await message.answer(
            "Пожалуйста, укажите место работы."
        )
        return

    await state.update_data(workplace=workplace)
    await state.set_state(DoctorRegistration.specialty)

    await message.answer(
        "Укажите вашу специальность:"
    )


@router.message(DoctorRegistration.specialty)
async def process_specialty(
    message: Message,
    state: FSMContext,
):
    specialty = (message.text or "").strip()

    if not specialty:
        await message.answer(
            "Пожалуйста, укажите специальность."
        )
        return

    await state.update_data(specialty=specialty)
    await state.set_state(
        DoctorRegistration.experience_years
    )

    await message.answer(
        "Сколько полных лет вы работаете врачом?"
    )


@router.message(DoctorRegistration.experience_years)
async def process_experience(
    message: Message,
    state: FSMContext,
):
    try:
        years = int((message.text or "").strip())

        if not 0 <= years < 80:
            raise ValueError

    except ValueError:
        await message.answer(
            "Введите опыт работы числом лет."
        )
        return

    data = await state.get_data()

    username = message.from_user.username

    # Перепроверяем на всякий случай: username мог быть на старте
    # регистрации, но пользователь мог убрать его в настройках
    # Telegram прямо посреди заполнения анкеты. Без username ссылка
    # t.me/<username> в карточке врача у пациента не будет работать.
    if not username:
        from handlers.start import NO_USERNAME_TEXT
        await state.clear()
        await message.answer(NO_USERNAME_TEXT)
        return

    await db.add_doctor(
        user_id=message.from_user.id,
        full_name=data["full_name"],
        city=data["city"],
        workplace=data["workplace"],
        specialty=data["specialty"],
        experience_years=years,
        username=username,
    )

    await state.clear()

    doctor = await db.get_doctor(
        message.from_user.id
    )

    await notify_admins_new_doctor(
        message.bot,
        doctor,
    )

    await message.answer(
        "✅ Анкета врача отправлена администратору.\n\n"
        "После одобрения вам станет доступен "
        "список пациентов.",
        reply_markup=get_doctor_menu_keyboard(
            is_admin=message.from_user.id in ADMIN_IDS
        ),
    )


# ============================================================
# СПИСОК ПАЦИЕНТОВ
# ============================================================

def patients_keyboard(patients):
    builder = InlineKeyboardBuilder()

    for patient in patients:
        username = patient["username"]

        if username:
            builder.row(
                InlineKeyboardButton(
                    text=f"💬 {patient['full_name']}",
                    url=f"https://t.me/{username}",
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=f"👤 {patient['full_name']}",
                    callback_data=(
                        f"patient_no_username:"
                        f"{patient['user_id']}"
                    ),
                )
            )

    return builder.as_markup()


@router.message(F.text == "👥 Список пациентов")
async def patient_list(message: Message):
    doctor = await db.get_doctor(
        message.from_user.id
    )

    if not doctor:
        return

    if doctor["status"] != "approved":
        await message.answer(
            "⏳ Доступ к списку пациентов появится "
            "после подтверждения вашей заявки."
        )
        return

    patients = await db.list_all_patients()

    if not patients:
        await message.answer(
            "👥 Пока нет зарегистрированных пациентов."
        )
        return

    await message.answer(
        f"👥 <b>Пациенты</b>\n\n"
        f"Всего пациентов: {len(patients)}\n\n"
        "Нажмите на пациента, чтобы открыть чат в Telegram.",
        reply_markup=patients_keyboard(patients),
    )


@router.callback_query(
    F.data.startswith("patient_no_username:")
)
async def patient_without_username(
    callback: CallbackQuery,
):
    await callback.answer(
        "У этого пациента не указан Telegram username.",
        show_alert=True,
    )