from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.states import DoctorRegistration
from database import db

from handlers.admin import notify_admins_new_doctor


router = Router(name="doctor_registration")


# ---------------------------------------------------------------------------
# ФИО
# ---------------------------------------------------------------------------

@router.message(DoctorRegistration.full_name)
async def process_full_name(
    message: Message,
    state: FSMContext,
):
    name = (message.text or "").strip()

    if not name or len(name) < 2:
        await message.answer(
            "Пожалуйста, введите корректное ФИО."
        )
        return

    await state.update_data(
        full_name=name
    )

    await state.set_state(
        DoctorRegistration.city
    )

    await message.answer(
        "В каком городе вы работаете?"
    )


# ---------------------------------------------------------------------------
# Город
# ---------------------------------------------------------------------------

@router.message(DoctorRegistration.city)
async def process_city(
    message: Message,
    state: FSMContext,
):
    city = (message.text or "").strip()

    if not city or len(city) < 2:
        await message.answer(
            "Пожалуйста, введите название города."
        )
        return

    await state.update_data(
        city=city
    )

    await state.set_state(
        DoctorRegistration.workplace
    )

    await message.answer(
        "Укажите место работы "
        "(клиника / больница):"
    )


# ---------------------------------------------------------------------------
# Место работы
# ---------------------------------------------------------------------------

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

    await state.update_data(
        workplace=workplace
    )

    await state.set_state(
        DoctorRegistration.specialty
    )

    await message.answer(
        "Укажите вашу специальность.\n\n"
        "Например: врач-эндокринолог"
    )


# ---------------------------------------------------------------------------
# Специальность
# ---------------------------------------------------------------------------

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

    await state.update_data(
        specialty=specialty
    )

    await state.set_state(
        DoctorRegistration.experience_years
    )

    await message.answer(
        "Каков ваш опыт работы "
        "(полных лет)?"
    )


# ---------------------------------------------------------------------------
# Опыт
# ---------------------------------------------------------------------------

@router.message(
    DoctorRegistration.experience_years
)
async def process_experience(
    message: Message,
    state: FSMContext,
):
    try:
        years = int(
            (message.text or "").strip()
        )

        if not 0 <= years < 80:
            raise ValueError

    except ValueError:
        await message.answer(
            "Пожалуйста, введите опыт работы "
            "числом лет.\n\n"
            "Например: 12"
        )
        return

    data = await state.get_data()

    user_id = message.from_user.id

    # В БД запись создаётся/обновляется
    # со статусом pending.
    #
    # Это также позволяет врачу, чья предыдущая
    # заявка была отклонена, зарегистрироваться
    # заново.
    await db.add_doctor(
        user_id=user_id,
        full_name=data["full_name"],
        city=data["city"],
        workplace=data["workplace"],
        specialty=data["specialty"],
        experience_years=years,
    )

    await state.clear()

    doctor = await db.get_doctor(user_id)

    # Отправляем заявку администраторам
    await notify_admins_new_doctor(
        message.bot,
        doctor,
    )

    await message.answer(
        "✅ <b>Анкета врача заполнена.</b>\n\n"
        f"👤 ФИО: {data['full_name']}\n"
        f"🏙 Город: {data['city']}\n"
        f"🏥 Место работы: {data['workplace']}\n"
        f"🩺 Специальность: {data['specialty']}\n"
        f"📅 Опыт работы: {years} лет\n\n"
        "⏳ Заявка отправлена администратору "
        "на проверку.\n\n"
        "После одобрения вы получите уведомление "
        "и сможете пользоваться функциями врача."
    )