from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.states import PatientRegistration
from keyboards.keyboards import (
    gender_keyboard,
    phone_keyboard,
    patient_menu_keyboard,
    remove_keyboard,
)
from database import db


router = Router(name="patient")


# ============================================================
# РЕГИСТРАЦИЯ
# ============================================================

@router.message(PatientRegistration.full_name)
async def process_full_name(
    message: Message,
    state: FSMContext,
):
    name = (message.text or "").strip()

    if not name or len(name) < 2:
        await message.answer(
            "Пожалуйста, введите корректное имя."
        )
        return

    await state.update_data(full_name=name)
    await state.set_state(PatientRegistration.gender)

    await message.answer(
        "Укажите ваш пол:",
        reply_markup=gender_keyboard,
    )


@router.message(
    PatientRegistration.gender,
    F.text.in_(["Мужской", "Женский"]),
)
async def process_gender(
    message: Message,
    state: FSMContext,
):
    await state.update_data(gender=message.text)

    await state.set_state(PatientRegistration.age)

    await message.answer(
        "Сколько вам лет?",
        reply_markup=remove_keyboard,
    )


@router.message(PatientRegistration.gender)
async def process_gender_invalid(message: Message):
    await message.answer(
        "Пожалуйста, выберите вариант с помощью кнопок.",
        reply_markup=gender_keyboard,
    )


@router.message(PatientRegistration.age)
async def process_age(
    message: Message,
    state: FSMContext,
):
    try:
        age = int((message.text or "").strip())

        if not 1 <= age <= 120:
            raise ValueError

    except ValueError:
        await message.answer(
            "Введите возраст цифрами, например: 34."
        )
        return

    await state.update_data(age=age)
    await state.set_state(PatientRegistration.city)

    await message.answer(
        "В каком городе вы проживаете?"
    )


@router.message(PatientRegistration.city)
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
    await state.set_state(PatientRegistration.diabetes_years)

    await message.answer(
        "Какой у вас стаж диабета в полных годах?"
    )


@router.message(PatientRegistration.diabetes_years)
async def process_diabetes_years(
    message: Message,
    state: FSMContext,
):
    try:
        years = int((message.text or "").strip())

        if not 0 <= years <= 100:
            raise ValueError

    except ValueError:
        await message.answer(
            "Введите количество лет цифрами."
        )
        return

    await state.update_data(diabetes_years=years)
    await state.set_state(PatientRegistration.height)

    await message.answer(
        "Укажите ваш рост в сантиметрах.\n"
        "Например: 170"
    )


@router.message(PatientRegistration.height)
async def process_height(
    message: Message,
    state: FSMContext,
):
    try:
        height = float(
            (message.text or "").strip().replace(",", ".")
        )

        if not 50 <= height <= 250:
            raise ValueError

    except ValueError:
        await message.answer(
            "Введите рост числом, например: 170."
        )
        return

    await state.update_data(height=height)
    await state.set_state(PatientRegistration.weight)

    await message.answer(
        "Укажите ваш вес в килограммах.\n"
        "Например: 65"
    )


@router.message(PatientRegistration.weight)
async def process_weight(
    message: Message,
    state: FSMContext,
):
    try:
        weight = float(
            (message.text or "").strip().replace(",", ".")
        )

        if not 2 <= weight <= 400:
            raise ValueError

    except ValueError:
        await message.answer(
            "Введите вес числом, например: 65."
        )
        return

    await state.update_data(weight=weight)
    await state.set_state(PatientRegistration.therapy)

    await message.answer(
        "Какую терапию вы получаете?\n"
        "Например: Инсулин НовоРапид + Тресиба"
    )


@router.message(PatientRegistration.therapy)
async def process_therapy(
    message: Message,
    state: FSMContext,
):
    therapy = (message.text or "").strip()

    if not therapy:
        await message.answer(
            "Пожалуйста, укажите терапию."
        )
        return

    await state.update_data(therapy=therapy)
    await state.set_state(PatientRegistration.phone)

    await message.answer(
        "Последний шаг — поделитесь номером телефона:",
        reply_markup=phone_keyboard,
    )


@router.message(
    PatientRegistration.phone,
    F.contact,
)
async def process_phone_contact(
    message: Message,
    state: FSMContext,
):
    phone = message.contact.phone_number

    await finish_patient_registration(
        message,
        state,
        phone,
    )


@router.message(
    PatientRegistration.phone,
    F.text,
)
async def process_phone_text(
    message: Message,
    state: FSMContext,
):
    phone = (message.text or "").strip()

    if len(phone) < 7:
        await message.answer(
            "Пожалуйста, введите корректный номер телефона.",
            reply_markup=phone_keyboard,
        )
        return

    await finish_patient_registration(
        message,
        state,
        phone,
    )


async def finish_patient_registration(
    message: Message,
    state: FSMContext,
    phone: str,
):
    data = await state.get_data()

    username = message.from_user.username

    await db.add_patient(
        user_id=message.from_user.id,
        full_name=data["full_name"],
        gender=data["gender"],
        age=data["age"],
        city=data["city"],
        diabetes_years=data["diabetes_years"],
        height_cm=data["height"],
        weight_kg=data["weight"],
        therapy=data["therapy"],
        phone=phone,
        username=username,
    )

    await state.clear()

    await message.answer(
        "✅ Регистрация завершена!\n\n"
        f"👤 Имя: {data['full_name']}\n"
        f"⚧ Пол: {data['gender']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"🏙 Город: {data['city']}\n"
        f"📅 Стаж диабета: {data['diabetes_years']} лет\n"
        f"📏 Рост: {data['height']} см\n"
        f"⚖️ Вес: {data['weight']} кг\n"
        f"💊 Терапия: {data['therapy']}\n"
        f"📞 Телефон: {phone}",
        reply_markup=patient_menu_keyboard,
    )


# ============================================================
# СВЯЗЬ С ВРАЧОМ
# ============================================================

def doctors_keyboard(doctors):
    builder = InlineKeyboardBuilder()

    for doctor in doctors:
        username = doctor["username"]

        if username:
            builder.row(
                InlineKeyboardButton(
                    text=f"👨‍⚕️ {doctor['full_name']}",
                    url=f"https://t.me/{username}",
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=f"👨‍⚕️ {doctor['full_name']}",
                    callback_data=f"doctor_no_username:{doctor['user_id']}",
                )
            )

    return builder.as_markup()


@router.message(F.text == "👨‍⚕️ Связь с врачом")
async def contact_doctor(message: Message):
    doctors = await db.list_approved_doctors()

    if not doctors:
        await message.answer(
            "👨‍⚕️ Сейчас нет подтверждённых врачей."
        )
        return

    await message.answer(
        "👨‍⚕️ <b>Выберите врача</b>\n\n"
        "Нажмите на врача, чтобы открыть чат в Telegram.",
        reply_markup=doctors_keyboard(doctors),
    )


@router.callback_query(
    F.data.startswith("doctor_no_username:")
)
async def doctor_without_username(callback):
    await callback.answer(
        "У этого врача не указан Telegram username.",
        show_alert=True,
    )