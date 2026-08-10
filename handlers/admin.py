from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS
from database import db

from keyboards.keyboards import (
    admin_menu_keyboard,
    get_admin_only_keyboard,
)


router = Router(name="admin")


ADMIN_BUTTON = "🔧 Админ панель"
DOCTORS_BUTTON = "👨‍⚕️ Список врачей"
PENDING_BUTTON = "📥 Заявки врачей"
BACK_BUTTON = "⬅️ Назад"


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


STATUS_LABELS = {
    "pending": "⏳ На рассмотрении",
    "approved": "✅ Одобрен",
    "rejected": "❌ Отклонён",
}


# ---------------------------------------------------------------------------
# Карточка врача
# ---------------------------------------------------------------------------

def build_doctor_card(
    doc,
    prefix: str = "",
):
    text = (
        f"{prefix}"
        f"👨‍⚕️ <b>{doc['full_name']}</b>\n"
        f"🏙 Город: {doc['city']}\n"
        f"🏥 Место работы: {doc['workplace']}\n"
        f"🩺 Специальность: {doc['specialty']}\n"
        f"📅 Опыт: {doc['experience_years']} лет\n"
        f"📌 Статус: "
        f"{STATUS_LABELS.get(doc['status'], doc['status'])}\n"
        f"🆔 ID: <code>{doc['user_id']}</code>"
    )

    builder = InlineKeyboardBuilder()

    if doc["status"] == "pending":

        builder.button(
            text="✅ Одобрить",
            callback_data=(
                f"adm_approve:{doc['user_id']}"
            ),
        )

        builder.button(
            text="❌ Отклонить",
            callback_data=(
                f"adm_reject:{doc['user_id']}"
            ),
        )

        builder.adjust(2)

    elif doc["status"] == "approved":

        builder.button(
            text="🗑 Удалить врача",
            callback_data=(
                f"adm_delete:{doc['user_id']}"
            ),
        )

        builder.adjust(1)

    return text, builder


# ---------------------------------------------------------------------------
# 🔧 Админ панель — постоянная Reply-кнопка
# ---------------------------------------------------------------------------

@router.message(F.text == ADMIN_BUTTON)
async def open_admin_panel(
    message: Message,
):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выберите нужный раздел:",
        reply_markup=admin_menu_keyboard(),
    )


# ---------------------------------------------------------------------------
# 📥 Заявки врачей
# ---------------------------------------------------------------------------

@router.message(F.text == PENDING_BUTTON)
async def show_pending_doctors(
    message: Message,
):
    if not is_admin(message.from_user.id):
        return

    pending = await db.get_pending_doctors()

    if not pending:
        await message.answer(
            "📥 <b>Заявки врачей</b>\n\n"
            "Новых заявок нет. ✅",
            reply_markup=admin_menu_keyboard(),
        )
        return

    await message.answer(
        f"📥 <b>Заявки врачей</b>\n\n"
        f"Новых заявок: {len(pending)}"
    )

    for doc in pending:

        text, builder = build_doctor_card(
            doc,
            prefix="🆕 <b>Новая заявка</b>\n\n",
        )

        await message.answer(
            text,
            reply_markup=builder.as_markup(),
        )


# ---------------------------------------------------------------------------
# 👨‍⚕️ Список подтверждённых врачей
# ---------------------------------------------------------------------------

@router.message(F.text == DOCTORS_BUTTON)
async def show_approved_doctors(
    message: Message,
):
    if not is_admin(message.from_user.id):
        return

    doctors = await db.list_approved_doctors()

    if not doctors:
        await message.answer(
            "👨‍⚕️ <b>Список врачей</b>\n\n"
            "Подтверждённых врачей пока нет.",
            reply_markup=admin_menu_keyboard(),
        )
        return

    await message.answer(
        f"👨‍⚕️ <b>Список врачей</b>\n\n"
        f"Подтверждённых врачей: {len(doctors)}"
    )

    for doc in doctors:

        text, builder = build_doctor_card(doc)

        await message.answer(
            text,
            reply_markup=builder.as_markup(),
        )


# ---------------------------------------------------------------------------
# ⬅️ Назад из админки
# ---------------------------------------------------------------------------

@router.message(F.text == BACK_BUTTON)
async def admin_back(
    message: Message,
):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "Главное меню.",
        reply_markup=get_admin_only_keyboard(),
    )


# ---------------------------------------------------------------------------
# Одобрение врача
# ---------------------------------------------------------------------------

@router.callback_query(
    F.data.startswith("adm_approve:")
)
async def approve_doctor(
    callback: CallbackQuery,
):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Недостаточно прав.",
            show_alert=True,
        )
        return

    doctor_id = int(
        callback.data.split(":")[1]
    )

    doctor = await db.get_doctor(doctor_id)

    if not doctor:
        await callback.answer(
            "Врач не найден.",
            show_alert=True,
        )
        return

    await db.set_doctor_status(
        doctor_id,
        "approved",
    )

    await callback.message.edit_text(
        callback.message.html_text
        + "\n\n"
        "✅ <b>Заявка одобрена.</b>",
        reply_markup=None,
    )

    await callback.answer(
        "Врач одобрен."
    )

    try:
        await callback.bot.send_message(
            doctor_id,
            "✅ <b>Ваша заявка врача одобрена!</b>\n\n"
            "Теперь вы зарегистрированы как "
            "подтверждённый врач.",
        )

    except Exception:
        pass


# ---------------------------------------------------------------------------
# Отклонение врача
# ---------------------------------------------------------------------------

@router.callback_query(
    F.data.startswith("adm_reject:")
)
async def reject_doctor(
    callback: CallbackQuery,
):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Недостаточно прав.",
            show_alert=True,
        )
        return

    doctor_id = int(
        callback.data.split(":")[1]
    )

    doctor = await db.get_doctor(doctor_id)

    if not doctor:
        await callback.answer(
            "Врач не найден.",
            show_alert=True,
        )
        return

    await db.set_doctor_status(
        doctor_id,
        "rejected",
    )

    await callback.message.edit_text(
        callback.message.html_text
        + "\n\n"
        "❌ <b>Заявка отклонена.</b>",
        reply_markup=None,
    )

    await callback.answer(
        "Заявка отклонена."
    )

    try:
        await callback.bot.send_message(
            doctor_id,
            "❌ <b>Ваша заявка врача отклонена.</b>\n\n"
            "При необходимости вы можете "
            "пройти регистрацию врача заново.",
        )

    except Exception:
        pass


# ---------------------------------------------------------------------------
# Удаление подтверждённого врача
# ---------------------------------------------------------------------------

@router.callback_query(
    F.data.startswith("adm_delete:")
)
async def delete_doctor_callback(
    callback: CallbackQuery,
):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Недостаточно прав.",
            show_alert=True,
        )
        return

    doctor_id = int(
        callback.data.split(":")[1]
    )

    doctor = await db.get_doctor(doctor_id)

    if not doctor:
        await callback.answer(
            "Врач уже удалён.",
            show_alert=True,
        )
        return

    await db.delete_doctor(
        doctor_id
    )

    await callback.message.edit_text(
        callback.message.html_text
        + "\n\n"
        "🗑 <b>Врач удалён из базы.</b>",
        reply_markup=None,
    )

    await callback.answer(
        "Врач удалён."
    )

    try:
        await callback.bot.send_message(
            doctor_id,
            "ℹ️ Ваша регистрация врача "
            "была удалена администратором.",
        )

    except Exception:
        pass


# ---------------------------------------------------------------------------
# Уведомление администраторов о новой заявке
# ---------------------------------------------------------------------------

async def notify_admins_new_doctor(
    bot: Bot,
    doctor,
) -> None:

    if not ADMIN_IDS:
        return

    if not doctor:
        return

    text, builder = build_doctor_card(
        doctor,
        prefix=(
            "🆕 <b>Новая заявка врача</b>\n\n"
        ),
    )

    for admin_id in ADMIN_IDS:

        try:
            await bot.send_message(
                admin_id,
                text,
                reply_markup=builder.as_markup(),
            )

        except Exception:
            pass