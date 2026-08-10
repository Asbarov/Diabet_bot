from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS
from database import db

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


STATUS_LABELS = {
    "pending": "⏳ На рассмотрении",
    "approved": "✅ Одобрен",
    "rejected": "❌ Отклонён",
}


def build_doctor_card(doc, prefix: str = "") -> tuple[str, "InlineKeyboardBuilder"]:
    text = (
        f"{prefix}"
        f"👨‍⚕️ <b>{doc['full_name']}</b>\n"
        f"🏙 Город: {doc['city']}\n"
        f"🏥 Место работы: {doc['workplace']}\n"
        f"🩺 Специальность: {doc['specialty']}\n"
        f"📅 Опыт: {doc['experience_years']} лет\n"
        f"📌 Статус: {STATUS_LABELS.get(doc['status'], doc['status'])}\n"
        f"🆔 ID: <code>{doc['user_id']}</code>"
    )

    builder = InlineKeyboardBuilder()
    if doc["status"] == "pending":
        builder.button(text="✅ Одобрить", callback_data=f"adm_approve:{doc['user_id']}")
        builder.button(text="❌ Отклонить", callback_data=f"adm_reject:{doc['user_id']}")
        builder.adjust(2)
    else:
        builder.button(text="🗑 Удалить врача", callback_data=f"adm_delete:{doc['user_id']}")
        builder.adjust(1)

    return text, builder


# ---------------------------------------------------------------------------
# Команды администратора
# ---------------------------------------------------------------------------

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return  # молча игнорируем — не выдаём наличие команды посторонним

    pending = await db.get_pending_doctors()
    if not pending:
        await message.answer("Заявок на рассмотрении нет. ✅")
        return

    await message.answer(f"📋 Заявок на рассмотрении: {len(pending)}")
    for doc in pending:
        text, builder = build_doctor_card(doc)
        await message.answer(text, reply_markup=builder.as_markup())


# Кнопка "🔧 Админ панель" в reply-клавиатуре открывает меню с двумя
# inline-кнопками — конкретные списки показываются уже после выбора.
# Работает независимо от того, есть ли у пользователя также роль
# пациента и/или врача — это отдельная, накладываемая привилегия.
@router.message(F.text == "🔧 Админ панель")
async def admin_panel_button(message: Message):
    if not is_admin(message.from_user.id):
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Заявки врачей", callback_data="adm_menu:pending")
    builder.button(text="👨‍⚕️ Список врачей", callback_data="adm_menu:all")
    builder.adjust(1)

    await message.answer("🔧 <b>Админ-панель</b>\n\nВыберите раздел:", reply_markup=builder.as_markup())


@router.callback_query(F.data == "adm_menu:pending")
async def admin_menu_pending(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    pending = await db.get_pending_doctors()
    if not pending:
        await callback.message.edit_text("Заявок на рассмотрении нет. ✅")
        await callback.answer()
        return

    await callback.message.edit_text(f"📋 Заявок на рассмотрении: {len(pending)}")
    for doc in pending:
        text, builder = build_doctor_card(doc)
        await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "adm_menu:all")
async def admin_menu_all(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    doctors = await db.list_all_doctors()
    if not doctors:
        await callback.message.edit_text("В базе пока нет ни одного врача.")
        await callback.answer()
        return

    await callback.message.edit_text(f"👨‍⚕️ Всего врачей в базе: {len(doctors)}")
    for doc in doctors:
        text, builder = build_doctor_card(doc)
        await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.message(Command("doctors"))
async def all_doctors(message: Message):
    if not is_admin(message.from_user.id):
        return

    doctors = await db.list_all_doctors()
    if not doctors:
        await message.answer("В базе пока нет ни одного врача.")
        return

    await message.answer(f"👨‍⚕️ Всего врачей в базе: {len(doctors)}")
    for doc in doctors:
        text, builder = build_doctor_card(doc)
        await message.answer(text, reply_markup=builder.as_markup())


# ---------------------------------------------------------------------------
# Обработка нажатий на кнопки
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("adm_approve:"))
async def approve_doctor(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    doctor_id = int(callback.data.split(":")[1])
    await db.set_doctor_status(doctor_id, "approved")

    await callback.message.edit_text(
        callback.message.html_text + "\n\n✅ <b>Заявка одобрена.</b>",
        reply_markup=None,
    )
    await callback.answer("Одобрено")

    try:
        await callback.bot.send_message(
            doctor_id,
            "✅ Ваша заявка на регистрацию врача одобрена администратором!\n"
            "Теперь вам доступен список пациентов, использующих бота.",
        )
    except Exception:
        pass  # пользователь мог заблокировать бота — не критично


@router.callback_query(F.data.startswith("adm_reject:"))
async def reject_doctor(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    doctor_id = int(callback.data.split(":")[1])
    await db.set_doctor_status(doctor_id, "rejected")

    await callback.message.edit_text(
        callback.message.html_text + "\n\n❌ <b>Заявка отклонена.</b>",
        reply_markup=None,
    )
    await callback.answer("Отклонено")

    try:
        await callback.bot.send_message(
            doctor_id,
            "❌ Ваша заявка на регистрацию врача была отклонена администратором.",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_delete:"))
async def delete_doctor_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    doctor_id = int(callback.data.split(":")[1])
    await db.delete_doctor(doctor_id)

    await callback.message.edit_text(
        callback.message.html_text + "\n\n🗑 <b>Врач удалён из базы.</b>",
        reply_markup=None,
    )
    await callback.answer("Удалено")


# ---------------------------------------------------------------------------
# Уведомление админов о новой заявке (вызывается из handlers/doctor_reg.py)
# ---------------------------------------------------------------------------

async def notify_admins_new_doctor(bot: Bot, doctor) -> None:
    if not ADMIN_IDS:
        return

    text, builder = build_doctor_card(doctor, prefix="🆕 <b>Новая заявка врача</b>\n\n")
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=builder.as_markup())
        except Exception:
            pass  # админ мог ещё не запустить бота (/start) — не критично
