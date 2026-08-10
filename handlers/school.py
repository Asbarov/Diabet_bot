from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from content.school_data import CATEGORIES

router = Router(name="diabetes_school")

CATEGORY_NAMES = list(CATEGORIES.keys())

MAX_MESSAGE_LEN = 4000  # с запасом от лимита Telegram в 4096 символов
BUTTON_LABEL_LEN = 60


def categories_keyboard():
    builder = InlineKeyboardBuilder()
    for idx, name in enumerate(CATEGORY_NAMES):
        builder.button(text=name, callback_data=f"sch_cat:{idx}")
    builder.adjust(1)
    return builder.as_markup()


def questions_keyboard(cat_idx: int):
    builder = InlineKeyboardBuilder()
    questions = CATEGORIES[CATEGORY_NAMES[cat_idx]]
    for q_idx, item in enumerate(questions):
        label = item["question"]
        if len(label) > BUTTON_LABEL_LEN:
            label = label[: BUTTON_LABEL_LEN - 1] + "…"
        builder.button(text=label, callback_data=f"sch_q:{cat_idx}:{q_idx}")
    builder.button(text="⬅️ К категориям", callback_data="sch_back")
    builder.adjust(1)
    return builder.as_markup()


def answer_keyboard(cat_idx: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ К списку вопросов", callback_data=f"sch_cat:{cat_idx}")
    builder.button(text="📂 К категориям", callback_data="sch_back")
    builder.adjust(1)
    return builder.as_markup()


@router.message(F.text == "📚 Школа диабета")
async def open_school(message: Message):
    await message.answer(
        "📚 <b>Школа диабета</b>\n\nВыберите категорию вопросов:",
        reply_markup=categories_keyboard(),
    )


@router.callback_query(F.data == "sch_back")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "📚 <b>Школа диабета</b>\n\nВыберите категорию вопросов:",
        reply_markup=categories_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sch_cat:"))
async def show_category(callback: CallbackQuery):
    cat_idx = int(callback.data.split(":")[1])
    name = CATEGORY_NAMES[cat_idx]
    await callback.message.edit_text(
        f"📂 <b>{name}</b>\n\nВыберите вопрос:",
        reply_markup=questions_keyboard(cat_idx),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sch_q:"))
async def show_answer(callback: CallbackQuery):
    _, cat_idx_s, q_idx_s = callback.data.split(":")
    cat_idx, q_idx = int(cat_idx_s), int(q_idx_s)
    item = CATEGORIES[CATEGORY_NAMES[cat_idx]][q_idx]

    text = f"❓ <b>{item['question']}</b>\n\n{item['answer']}"
    if len(text) > MAX_MESSAGE_LEN:
        text = text[: MAX_MESSAGE_LEN - 1] + "…"

    await callback.message.edit_text(text, reply_markup=answer_keyboard(cat_idx))
    await callback.answer()
