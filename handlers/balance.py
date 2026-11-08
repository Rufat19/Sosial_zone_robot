import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from handlers.payment import PAYMENT_PACKAGES
from handlers.balance_utils import get_balance
from handlers.start import get_main_buttons

router = Router()

@router.message(F.text == "/balance")
async def balance_query(message: Message):
    if message.from_user is None:
        await message.answer("İstifadəçi məlumatı tapılmadı.")
        return
    user_id = message.from_user.id
    balance = get_balance(user_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👛 Balansı göstər", callback_data="show_balance")],
            [InlineKeyboardButton(text="💳 Balansı artır", callback_data="fill_balance")]
        ]
    )
    await message.answer(f"💰 Sənin balansın: <b>{balance}</b> RBCron — nə etmək istəyirsən?", parse_mode="HTML", reply_markup=keyboard)

@router.callback_query(F.data == "show_balance")
async def show_balance_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = get_balance(user_id)
    if callback.message is not None:
        msg = await callback.message.answer(f"💰 Sizin balansınız: <b>{balance}</b> RBCron", parse_mode="HTML")
        await asyncio.sleep(7)
        try:
            await msg.delete()
        except Exception:
            pass
    await callback.answer()

@router.callback_query(F.data == "fill_balance")
async def fill_balance_callback(callback: CallbackQuery):
    if callback.message is not None:
        user_id = callback.from_user.id
        balance = get_balance(user_id)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{amount:g} RBCron — ${price / 100:g}",
                        callback_data=f"buy_rbc_{package_id}",
                    )
                ]
                for package_id, (amount, price) in PAYMENT_PACKAGES.items()
            ]
            + [[InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")]]
        )
        await callback.message.answer(
            (
                "💳 Balansı Telegram Payments vasitəsilə artırın.\n\n"
                "🔹 <b>Paket seçin:</b>\n"
                "• 5 RBCron — $5\n"
                "• 20 RBCron — $10\n"
                "• 50 RBCron — $20\n\n"
                f"💰 Cari balansınız: <b>{balance}</b> RBCron\n\n"
                "Ödəniş Telegram daxilində tamamlandıqdan sonra balansınız avtomatik artırılacaq."
            ),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    if callback.message:
        await callback.message.answer("Aşağıdakı seçimlərdən birini seçin və bütün funksiyalara rahat giriş əldə edin:", reply_markup=get_main_buttons())
    await callback.answer()