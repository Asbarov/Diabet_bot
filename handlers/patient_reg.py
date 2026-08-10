from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.states import PatientRegistration
from keyboards.keyboards import (
    gender_keyboard,
    phone_keyboard,
    patient_menu_keyboard,
    remove_keyboard,
)
from database import db

router = Router(name="patient_registration")


# ---------------------------------------------------------------------------
# ФИО / имя
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer("Пожалуйста, введите корректное имя (минимум 2 символа).")
        return

    await state.update_data(full_name=name)
    await state.set_state(PatientRegistration.gender)
    await message.answer("Укажите ваш пол:", reply_markup=gender_keyboard)


# ---------------------------------------------------------------------------
# Пол
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.gender, F.text.in_(["Мужской", "Женский"]))
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await state.set_state(PatientRegistration.age)
    await message.answer("Сколько вам лет?", reply_markup=remove_keyboard)


@router.message(PatientRegistration.gender)
async def process_gender_invalid(message: Message):
    await message.answer(
        "Пожалуйста, выберите пол, используя кнопки ниже.",
        reply_markup=gender_keyboard,
    )


# ---------------------------------------------------------------------------
# Возраст
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if not (0 < age < 120):
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите возраст цифрами (например, 34).")
        return

    await state.update_data(age=age)
    await state.set_state(PatientRegistration.city)
    await message.answer("В каком городе вы проживаете?")


# ---------------------------------------------------------------------------
# Город
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    if not city or len(city) < 2:
        await message.answer("Пожалуйста, введите название города.")
        return

    await state.update_data(city=city)
    await state.set_state(PatientRegistration.diabetes_years)
    await message.answer("Какой у вас стаж диабета (полных лет)?")


# ---------------------------------------------------------------------------
# Стаж диабета
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.diabetes_years)
async def process_diabetes_years(message: Message, state: FSMContext):
    try:
        years = int(message.text.strip())
        if not (0 <= years < 100):
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите стаж диабета числом лет (например, 5).")
        return

    await state.update_data(diabetes_years=years)
    await state.set_state(PatientRegistration.height)
    await message.answer("Укажите ваш рост в см (например, 170):")


# ---------------------------------------------------------------------------
# Рост
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = float(message.text.strip().replace(",", "."))
        if not (50 <= height <= 250):
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите рост в сантиметрах числом (например, 170).")
        return

    await state.update_data(height=height)
    await state.set_state(PatientRegistration.weight)
    await message.answer("Укажите ваш вес в кг (например, 65):")


# ---------------------------------------------------------------------------
# Вес
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.strip().replace(",", "."))
        if not (2 <= weight <= 400):
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите вес в килограммах числом (например, 65).")
        return

    await state.update_data(weight=weight)
    await state.set_state(PatientRegistration.therapy)
    await message.answer(
        "Какую терапию (препараты) вы получаете?\n"
        "Например: «Инсулин НовоРапид + Тресиба» или «Метформин»."
    )


# ---------------------------------------------------------------------------
# Терапия
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.therapy)
async def process_therapy(message: Message, state: FSMContext):
    therapy = message.text.strip()
    if not therapy:
        await message.answer("Пожалуйста, укажите препараты терапии.")
        return

    await state.update_data(therapy=therapy)
    await state.set_state(PatientRegistration.phone)
    await message.answer(
        "И последний шаг — поделитесь номером телефона, нажав на кнопку ниже, "
        "или введите его вручную.",
        reply_markup=phone_keyboard,
    )


# ---------------------------------------------------------------------------
# Телефон (через кнопку "поделиться контактом")
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await finish_patient_registration(message, state, phone)


# ---------------------------------------------------------------------------
# Телефон (вручную текстом)
# ---------------------------------------------------------------------------
@router.message(PatientRegistration.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    digits = "".join(ch for ch in phone if ch.isdigit() or ch == "+")
    if len(digits) < 7:
        await message.answer(
            "Похоже, номер введён некорректно. Отправьте номер телефона "
            "текстом (например, +79991234567) или нажмите кнопку ниже.",
            reply_markup=phone_keyboard,
        )
        return

    await finish_patient_registration(message, state, digits)


async def finish_patient_registration(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()

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
    )
    await state.clear()

    await message.answer(
        "✅ Регистрация завершена! Карта пациента сохранена.\n\n"
        f"👤 Имя: {data['full_name']}\n"
        f"⚧ Пол: {data['gender']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"🏙 Город: {data['city']}\n"
        f"📅 Стаж диабета: {data['diabetes_years']} лет\n"
        f"📏 Рост: {data['height']} см\n"
        f"⚖️ Вес: {data['weight']} кг\n"
        f"💊 Терапия: {data['therapy']}\n"
        f"📞 Телефон: {phone}\n\n"
        "Теперь вам доступны следующие функции:",
        reply_markup=patient_menu_keyboard,
    )
