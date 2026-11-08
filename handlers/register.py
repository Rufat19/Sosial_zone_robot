import re
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, CARD_NUMBER
from database.db import get_db_connection

register_router = Router()

class RegisterForm(StatesGroup):
    entering_name = State()
    entering_phone = State()
    awaiting_screenshot = State()

class FeedbackForm(StatesGroup):
    waiting_feedback = State()

def get_buttons():
    return [
        [InlineKeyboardButton(text="💬 Şikayət və təklif", callback_data="feedback")],
        [
            InlineKeyboardButton(text="👤 Adminlə əlaqə", callback_data="contact_admin")
        ]
    ]

@register_router.message(F.text == "/start")
async def start_menu(message: Message, state: FSMContext):
    await message.answer(
        "Salam! Seçim edin:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=get_buttons()),
    )
    await state.clear()

@register_router.message(RegisterForm.entering_name)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    await state.update_data(name=name)
    await message.answer("Telefon nömrənizi daxil edin (məsələn: +994501234567).")
    await state.set_state(RegisterForm.entering_phone)

@register_router.message(RegisterForm.entering_phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.text.strip() if message.text else ""
    if not re.match(r"^\+994\d{9}$", phone):
        await message.answer("Telefon nömrəsi +994 ilə başlamalı və 9 rəqəm davam etməlidir.")
        return
    await state.update_data(phone=phone)
    await message.answer("Ödənişi tamamlayın, sonra qəbzin şəklini göndərin.\n\n"
        f"💳 Kart nömrəsi: <b>{CARD_NUMBER}</b>\n\n"
        "✅ Ödənişi tamamladıqdan sonra screenshot/qəbzi bu çatda paylaşın.")
    await state.set_state(RegisterForm.awaiting_screenshot)

@register_router.message(RegisterForm.awaiting_screenshot)
async def process_payment_proof(message: Message, state: FSMContext):
    # Yalnız şəxsi mesajlarda qəbz qəbul et
    if message.chat.type != "private":
        return
    
    data = await state.get_data()
    if message.content_type != ContentType.PHOTO or not message.photo:
        await message.answer("❗ Zəhmət olmasa, yalnız ödəniş qəbzinin şəklini göndərin.")
        return
    user = message.from_user
    if user is None:
        await message.answer("❗ İstifadəçi məlumatı tapılmadı. Zəhmət olmasa, yenidən cəhd edin.")
        return
    user_id = user.id
    username = getattr(user, "username", None) or "Yoxdur"
    username_line = f"🔗 Username: @{username}" if username != "Yoxdur" else "🔗 Username: Yoxdur"
    caption = (
        f"✅ Yeni qeydiyyat və ödəniş screenshotu:\n"
        f"👤 Ad, Soyad: {data['name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"🆔 Telegram ID: {user_id}\n"
        f"{username_line}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Təsdiqlə", callback_data=f"approve_{user_id}")]
    ])
    from config import ADMIN_ID
    from aiogram import Bot
    bot = message.bot if hasattr(message, "bot") and message.bot is not None else None
    if ADMIN_ID is not None and bot is not None:
        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption, reply_markup=keyboard)
    else:
        await message.answer("❗ Admin ID is not set or bot instance is unavailable. Cannot send payment proof to admin.")
    with get_db_connection() as conn:
        with conn:
            conn.execute(
                     """INSERT INTO users (user_id, name, phone, username) VALUES (%s, %s, %s, %s)
                         ON CONFLICT (user_id) DO UPDATE
                         SET name=EXCLUDED.name, phone=EXCLUDED.phone, username=EXCLUDED.username""",
                (user_id, data['name'], data['phone'], username)
            )
    await message.answer("✅ Qeydiyyat tamamlandı. Məlumat adminə göndərildi.")
    await message.answer("📨 Təsdiqdən sonra sizə bir istifadəçi üçün nəzərdə tutulmuş və 24 saat ərzində keçərli olan giriş linki təqdim olunacaq.")
    await state.clear()

@register_router.message(F.text == "/test_inline")
async def test_inline(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Test", callback_data="test_callback")]
        ]
    )
    await message.answer("Inline test:", reply_markup=keyboard)

@register_router.callback_query(F.data == "test_callback")
async def test_callback_handler(callback: CallbackQuery):
    await callback.answer("Test düyməsinə basdınız!")

@register_router.callback_query(F.data == "feedback")
async def feedback_callback(callback: CallbackQuery, state: FSMContext):
    if callback.message:
        await callback.message.answer("Şikayət və ya təklifinizi yazın.")
        await state.set_state(FeedbackForm.waiting_feedback)
    await callback.answer()

@register_router.message(FeedbackForm.waiting_feedback)
async def process_feedback(message: Message, state: FSMContext):
    feedback_text = message.text
    # Burada adminə göndərə bilərsən, məsələn:
    from config import ADMIN_ID
    sender_name = message.from_user.full_name if message.from_user and hasattr(message.from_user, "full_name") else "Naməlum"
    sender_id = message.from_user.id if message.from_user and hasattr(message.from_user, "id") else "Naməlum"
    if ADMIN_ID is not None and message.bot is not None:
        await message.bot.send_message(ADMIN_ID, f"Yeni şikayət/təklif:\n{feedback_text}\nGöndərən: {sender_name} ({sender_id})")
    else:
        await message.answer("Admin ID tapılmadı və ya bot instance mövcud deyil, şikayət/təklif göndərilə bilmədi.")
    await message.answer("Təşəkkür edirəm. Müraciətiniz Adminə göndərildi.")
    await state.clear()

@register_router.callback_query(F.data == "contact_admin")
async def contact_admin_callback(callback: CallbackQuery, state: FSMContext):
    text = "Adminlə əlaqə: @Rufat19"
    if callback.message is not None:
        await callback.message.answer(text)
    await callback.answer()

@register_router.message(F.text == "/test")
async def test_command(message: Message, state: FSMContext):
    await message.answer("Test əmri aktiv deyil.")

@register_router.message(F.text == "/register")
async def register_start(message: Message, state: FSMContext):
    await message.answer("Ad və soyadınızı daxil edin.")
    await state.set_state(RegisterForm.entering_name)