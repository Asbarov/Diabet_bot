from aiogram.fsm.state import State, StatesGroup


class PatientRegistration(StatesGroup):
    full_name = State()
    gender = State()
    age = State()
    city = State()
    diabetes_years = State()
    height = State()
    weight = State()
    therapy = State()
    phone = State()


class DoctorRegistration(StatesGroup):
    full_name = State()
    city = State()
    workplace = State()
    specialty = State()
    experience_years = State()
