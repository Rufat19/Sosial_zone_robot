from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, CARD_NUMBER
import os
from dotenv import load_dotenv
from handlers.balance_utils import get_balance, set_balance
from handlers.start import get_main_buttons

load_dotenv()

router = Router()

class QuizForm(StatesGroup):
    waiting_name = State()
    waiting_receipt = State()

class QuizRejectForm(StatesGroup):
    waiting_reason = State()

QUIZ_TOPICS = sorted([
    ("Pensiya- 50 TEST", "quiz_pensiya"),
    ("Müavinət- 50 TEST", "quiz_müavinət"),
    ("Təqaüd- 50 TEST", "quiz_təqaüd"),
    ("Fərdi Məlumatlar- 50 TEST", "quiz_fərdi"),
    ("Müraciətlərə baxılması- 50 TEST", "quiz_müraciətlər"),
], key=lambda x: x[0])

QUIZ_LINKS = {
    "quiz_pensiya": "https://t.me/Sosial_Zone_Robot/pensiya",
    "quiz_müavinət": "https://t.me/Sosial_Zone_Robot/muavinet",
    "quiz_təqaüd": "https://t.me/Sosial_Zone_Robot/kompensasiya",
    "quiz_fərdi": "https://t.me/Sosial_Zone_Robot/personal",
    "quiz_müraciətlər": "https://t.me/Sosial_Zone_Robot/request",
}

@router.callback_query(F.data == "quiz")
async def quiz_callback(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=
            [[InlineKeyboardButton(text=topic, callback_data=cb)] for topic, cb in QUIZ_TOPICS] +
            [[InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]]
    )
    if callback.message:
        await callback.message.answer("Sınaq imtahanı mövzusunu seçin:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.in_([cb for _, cb in QUIZ_TOPICS]))
async def quiz_topic_selected(callback: CallbackQuery, state: FSMContext):
    await state.update_data(quiz_topic=callback.data)
    await state.set_state(QuizForm.waiting_name)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Razıyam", callback_data="quiz_accept"),
                InlineKeyboardButton(text="💳 Balansı artır", callback_data="fill_balance")
            ],
            [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]
        ]
    )
    if callback.message:
        await callback.message.answer(
            "Bu əməliyyat üçün sizdən <b>50 RBCron</b> çıxılacaq. Razısınız?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "quiz_accept")
async def quiz_accept_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    topic = data.get("quiz_topic", "")
    user_id = callback.from_user.id
    coin_required = 50  # bütün quizlər üçün qiymət 50 RBCron
    balance = get_balance(user_id)
    if balance < coin_required:
        if callback.message is not None:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Balansı artır", callback_data="fill_balance")],
                    [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]
                ]
            )
            await callback.message.answer(
                f"<b>Balansınızda kifayət qədər RBCron yoxdur.</b>\n"
                f"Sınaq imtahanına giriş üçün <b>{coin_required} RBCron</b> lazımdır.\n"
                f"Balansınızı artırmaq üçün <b>Balansı artır</b> düyməsinə klikləyin.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        await state.clear()
        await callback.answer()
        return
    set_balance(user_id, balance - coin_required)
    link = QUIZ_LINKS.get(topic, "https://t.me/default_link")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sınaq imtahanına başla", url=link)],
            [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]
        ]
    )
    if callback.message is not None:
        await callback.message.answer(
            f"Sınaq imtahanına giriş təsdiqləndi!\nMövzu: {topic}\n"
            f"Balansınızdan {coin_required} RBCron çıxıldı. Yeni balans: {balance - coin_required} RBCron",
            reply_markup=keyboard
        )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "quiz_decline")
async def quiz_decline_callback(callback: CallbackQuery, state: FSMContext):
    if callback.message is not None:
        main_menu_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]
            ]
        )
        await callback.message.answer("Əməliyyat ləğv olundu. Balansınızdan heç nə çıxılmadı.", reply_markup=main_menu_kb)
    await state.clear()
    await callback.answer()

@router.message(QuizForm.waiting_name)
async def quiz_name_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    topic = data.get("quiz_topic", "")
    user_id = message.from_user.id if message.from_user is not None else None
    if user_id is None:
        await message.answer("İstifadəçi məlumatı tapılmadı.")
        await state.clear()
        return
    coin_required = 50  # bütün quizlər üçün qiymət 50 RBCron
    balance = get_balance(user_id)
    if balance < coin_required:
        await message.answer(
            f"<b>Balansınızda kifayət qədər RBCron yoxdur.</b>\n"
            f"Sınaq imtahanına giriş üçün <b>{coin_required} RBCron</b> lazımdır.\n"
            f"Balansınızı artırmaq üçün <b>Balans</b> bölməsinə keçin və ödəniş edin.",
            parse_mode="HTML"
        )
        await state.clear()
        return
    set_balance(user_id, balance - coin_required)
    link = QUIZ_LINKS.get(topic, "https://t.me/default_link")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sınaq imtahanına başla", url=link)],
            [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]
        ]
    )
    await message.answer(
        f"Sınaq imtahanına giriş təsdiqləndi!\nMövzu: {topic}\n"
        f"Balansınızdan {coin_required} RBCron çıxıldı. Yeni balans: {balance - coin_required} RBCron",
        reply_markup=keyboard
    )
    await state.clear()

@router.message(QuizForm.waiting_receipt)
async def quiz_receipt_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    topic = data.get("quiz_topic")
    user_id = message.from_user.id if message.from_user is not None else None
    if user_id is None:
        await message.answer("İstifadəçi məlumatı tapılmadı.")
        return
    if not message.photo:
        await message.answer("Zəhmət olmasa, ödəniş qəbzinin şəklini göndərin.")
        return
    photo_id = message.photo[-1].file_id
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Təsdiqlə", callback_data=f"quiz_confirm_{user_id}_{topic}"),
                InlineKeyboardButton(text="Rədd et", callback_data=f"quiz_reject_{user_id}_{topic}")
            ]
        ]
    )
    if ADMIN_ID is not None:
        bot = message.bot if message.bot is not None else (message._bot if hasattr(message, "_bot") else None)
        if bot is not None:
            await bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_id,
                caption=(
                    f"Sınaq imtahanı üçün yeni müraciət:\n"
                    f"Ad Soyad: {name}\n"
                    f"Mövzu: {topic}\n"
                    f"Telegram ID: {user_id}\n"
                    f"Qəbz: [şəkil]"
                ),
                reply_markup=keyboard
            )
            await message.answer("Qəbz göndərildi! Admin təsdiqlədikdən sonra giriş linki təqdim olunacaq. Səbirli olun.")
        else:
            await message.answer("Bot obyektinə çatmaq mümkün olmadı, qəbz göndərilə bilmədi.")
    else:
        await message.answer("Admin ID tapılmadı, qəbz göndərilə bilmədi.")
    await state.clear()

@router.callback_query(F.data.startswith("quiz_confirm_"))
async def quiz_confirm_callback(callback: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    if callback.data is None:
        if callback.message is not None:
            await callback.message.answer("Callback məlumatı tapılmadı.")
        await callback.answer()
        return
    parts = callback.data.split("_")
    user_id = parts[2]
    topic = "_".join(parts[3:])
    link = QUIZ_LINKS.get(topic, "https://t.me/default_link")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sınaq imtahanına başla", url=link)],
            [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]
        ]
    )
    bot = callback.bot if callback.bot is not None else (callback._bot if hasattr(callback, "_bot") else None)
    if bot is not None:
        await bot.send_message(
            int(user_id),
            f"Sınaq imtahanına giriş təsdiqləndi!\nMövzu: {topic}",
            reply_markup=keyboard
        )
        if callback.message is not None:
            await callback.message.answer("Təsdiqləndi və iştirakçıya giriş buttonu göndərildi.")
    else:
        if callback.message is not None:
            await callback.message.answer("Bot obyektinə çatmaq mümkün olmadı, mesaj göndərilə bilmədi.")
    await callback.answer()

@router.callback_query(F.data.startswith("quiz_reject_"))
async def quiz_reject_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data is None:
        if callback.message is not None:
            await callback.message.answer("Callback məlumatı tapılmadı.")
        await callback.answer()
        return
    parts = callback.data.split("_")
    user_id = parts[2]
    await state.set_state(QuizRejectForm.waiting_reason)
    await state.update_data(reject_user_id=user_id)
    if callback.message is not None:
        await callback.message.answer("Rədd səbəbini yazın:")
    await callback.answer()

@router.message(QuizRejectForm.waiting_reason)
async def quiz_reject_reason_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reject_user_id")
    reason = message.text
    if user_id is not None:
        bot = message.bot if message.bot is not None else (message._bot if hasattr(message, "_bot") else None)
        if bot is not None:
            await bot.send_message(
                int(user_id),
                f"Sınaq imtahanına giriş admin tərəfindən rədd edildi.\nSəbəb: {reason}"
            )
            await message.answer("Rədd səbəbi iştirakçıya göndərildi.")
        else:
            await message.answer("Bot obyektinə çatmaq mümkün olmadı, mesaj göndərilə bilmədi.")
    else:
        await message.answer("İştirakçının ID-si tapılmadı, mesaj göndərilə bilmədi.")
    await state.clear()