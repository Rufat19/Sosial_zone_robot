from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, CARD_NUMBER
from handlers.balance_utils import get_balance, set_balance

router = Router()

class QuizWorldForm(StatesGroup):
    waiting_name = State()
    waiting_receipt = State()

QUIZ_WORLD_TOPICS = [
    ("Dünya görüşü I- 50 TEST", "quiz_world"),
    ("Dünya görüşü II- 50 TEST", "quiz_world2"),
    ("Dünya görüşü III- 50 TEST", "quiz_world3"),
    ("Dünya görüşü IV- 50 TEST", "quiz_world4")
]

QUIZ_WORLD_LINKS = {
    "quiz_world": "https://wayground.com/pro/join/quiz/689268eb0948ddc0039469ab/start?studentShare=true",
    "quiz_world2": "https://wayground.com/pro/join/quiz/688a15d9cffd60776542e57c/start?studentShare=true",
    "quiz_world3": "https://wayground.com/pro/join/quiz/68a19900e677276cef66e8fb/start?studentShare=true",
    "quiz_world4": "https://wayground.com/pro/join/quiz/68a198cacf5d2cb182633ca6/start?studentShare=true",
}

@router.callback_query(F.data == "quiz_world_menu")
async def quiz_world_menu_callback(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=
            [[InlineKeyboardButton(text=topic, callback_data=cb)] for topic, cb in QUIZ_WORLD_TOPICS] +
            [[InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]]
    )
    if callback.message:
        await callback.message.answer("Dünya görüşü test mövzusunu seçin:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.in_([cb for _, cb in QUIZ_WORLD_TOPICS]))
async def quiz_world_topic_selected(callback: CallbackQuery, state: FSMContext):
    await state.update_data(quiz_topic=callback.data)
    await state.set_state(QuizWorldForm.waiting_name)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Razıyam", callback_data="quiz_world_accept"),
                InlineKeyboardButton(text="💳 Balansı artır", callback_data="fill_balance")
            ],
            [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]
        ]
    )
    if callback.message:
        user_id = callback.from_user.id
        balance = get_balance(user_id)
        await callback.message.answer(
            f"Bu əməliyyat üçün sizdən <b>70 RBCron</b> çıxılacaq. Razısınız?\nCari balansınız: <b>{balance} RBCron</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "quiz_world_accept")
async def quiz_world_accept_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    topic = data.get("quiz_topic", "")
    user_id = callback.from_user.id
    coin_required = 70  # bütün dünya görüşü quizləri üçün qiymət 70 RBCron
    balance = get_balance(user_id)
    if balance < coin_required:
        if callback.message is not None:
            await callback.message.answer(
                f"<b>Balansınızda kifayət qədər RBCron yoxdur.</b>\n"
                f"Sınaq imtahanına giriş üçün <b>{coin_required} RBCron</b> lazımdır.\n"
                f"Balansınızı artırmaq üçün <b>Balans</b> bölməsinə keçin və ödəniş edin.",
                parse_mode="HTML"
            )
        await state.clear()
        await callback.answer()
        return
    set_balance(user_id, balance - coin_required)
    link = QUIZ_WORLD_LINKS.get(topic, "https://t.me/default_link")
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

@router.callback_query(F.data == "quiz_world_decline")
async def quiz_world_decline_callback(callback: CallbackQuery, state: FSMContext):
    if callback.message is not None:
        main_menu_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]
            ]
        )
        await callback.message.answer("Əməliyyat ləğv olundu. Balansınızdan heç nə çıxılmadı.", reply_markup=main_menu_kb)
    await state.clear()
    await callback.answer()
