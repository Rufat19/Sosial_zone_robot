from handlers.start import get_main_buttons
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_db_connection

router = Router()

# Yeni "istifadəçi rəyləri" menyusu üçün handler
@router.callback_query(F.data == "reviews_menu")
async def reviews_menu_callback(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍️ Rəy yaz", callback_data="review"),
                InlineKeyboardButton(text="📚 Bütün rəylər", callback_data="show_reviews"),
            ],
            [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]
        ]
    )
    if callback.message:
        await callback.message.answer("🌟 Rəylər — sənin fikrin dəyərlidir!", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    if callback.message:
        await callback.message.answer("Aşağıdakı seçimlərdən birini seçin və bütün funksiyalara rahat giriş əldə edin:", reply_markup=get_main_buttons())
    await callback.answer()

class ReviewForm(StatesGroup):
    waiting_rating = State()
    waiting_text = State()

def save_review(user_id, rating, text, username=None, full_name=None, reply=None):
    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO reviews (user_id, rating, text, username, full_name, reply)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, rating, text, username, full_name, reply),
        )

def get_all_reviews():
    with get_db_connection() as conn:
        return conn.execute(
            """SELECT id, user_id, rating, text, username, full_name, reply
               FROM reviews ORDER BY id"""
        ).fetchall()

@router.callback_query(F.data == "review")
async def review_callback(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5"), InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4")],
            [InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3"), InlineKeyboardButton(text="⭐⭐", callback_data="rate_2")],
            [InlineKeyboardButton(text="⭐", callback_data="rate_1")],
        ]
    )
    await state.set_state(ReviewForm.waiting_rating)
    if callback.message:
        await callback.message.answer("Qiymətləndirmə üçün ulduz seçin:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("rate_"))
async def rate_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data is not None:
        rating = int(callback.data.split("_")[1])
        await state.update_data(rating=rating)
        await state.set_state(ReviewForm.waiting_text)
        if callback.message:
            await callback.message.answer("Rəyinizi yazın — qısa və səmimi 😊")
        await callback.answer()
    else:
        if callback.message:
            await callback.message.answer("Xəta baş verdi: rating məlumatı tapılmadı.")
        await callback.answer()

@router.message(ReviewForm.waiting_text)
async def review_text(message: Message, state: FSMContext):
    data = await state.get_data()
    rating = data.get("rating")
    text = message.text
    user_id = message.from_user.id if message.from_user else "unknown"
    username = message.from_user.username if message.from_user else None
    full_name = message.from_user.full_name if message.from_user else None
    save_review(user_id, rating, text, username=username, full_name=full_name)
    main_menu_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Ana menyu", callback_data="main_menu")]
        ]
    )
    await message.answer("Təşəkkürlər! 🌟 Rəyiniz qeyd olundu — qiymətləndirməniz bizi inkişaf etdirir.", reply_markup=main_menu_kb)
    await state.clear()

@router.callback_query(F.data == "show_reviews")
async def show_reviews_callback(callback: CallbackQuery, state: FSMContext):
    import asyncio
    reviews = get_all_reviews()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]]
    )
    if not reviews:
        if callback.message:
            await callback.message.answer("📭 Hələ ki, rəy yoxdur — sən ilk ol!", reply_markup=kb)
    else:
        lines = []
        for idx, r in enumerate(reviews, 1):
            stars = "⭐" * int(r.get("rating", 0))
            name = r.get("full_name") or ("@" + r.get("username") if r.get("username") else str(r.get("user_id", "")))
            reply_txt = r.get("reply")
            block = f"{idx}) {stars} — {name}\n{r.get('text','')}"
            if reply_txt:
                block += f"\n🗨️ Admin: {reply_txt}"
            lines.append(block)
        msg_text = "\n\n".join(lines)
        if callback.message:
            await callback.message.answer(msg_text, reply_markup=kb)
    await callback.answer()

# Admin cavab vermək üçün (ADMIN_ID ilə yoxla)
class AdminReplyForm(StatesGroup):
    waiting_reply = State()

@router.callback_query(F.data.startswith("admin_reply_"))
async def admin_reply_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data is not None:
        review_idx = int(callback.data.split("_")[-1])
        await state.set_state(AdminReplyForm.waiting_reply)
        await state.update_data(review_idx=review_idx)
        if callback.message:
            await callback.message.answer("Rəy üçün cavabınızı yazın:")
    else:
        if callback.message:
            await callback.message.answer("Xəta baş verdi: review_idx məlumatı tapılmadı.")
    await callback.answer()

@router.message(AdminReplyForm.waiting_reply)
async def process_admin_reply(message: Message, state: FSMContext):
    from config import ADMIN_ID
    if not message.from_user or message.from_user.id != ADMIN_ID:
        await message.answer("Yalnız admin cavab verə bilər.")
        await state.clear()
        return
    data = await state.get_data()
    review_idx = data.get("review_idx")
    reviews = get_all_reviews()
    if review_idx is not None and isinstance(review_idx, int) and 0 <= review_idx < len(reviews):
        review = reviews[review_idx]
        with get_db_connection() as conn:
            conn.execute("UPDATE reviews SET reply=%s WHERE id=%s", (message.text, review["id"]))
        # istifadəçiyə xəbər göndərək (əgər username/id varsa)
        target = review.get("user_id")
        try:
            if target:
                await message.bot.send_message(int(target), f"🗨️ Admin cavab verdi: {message.text}")
        except Exception:
            pass
        await message.answer("Cavab əlavə olundu və istifadəçiyə göndərildi (əgər mümkün olduysa).")
    else:
        await message.answer("Rəy tapılmadı.")
    await state.clear()