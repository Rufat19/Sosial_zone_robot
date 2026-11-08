from handlers.start import get_main_buttons
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import asyncio
from handlers.start import main_menu_keyboard

router = Router()

def get_text(key: str) -> str:
    texts = {
        "about_channels_info": (
            "<b>Faydalı kanallar seçimi</b>\n\n"
            "Aşağıdakı kanallar sosial sahədə gündəlik işinizi asanlaşdıracaq.\n"
            "Mövzular: qanunvericilik yenilikləri, hesabat nümunələri, praktiki məsləhətlər."
        ),
        "channel_sosial_muhit": (
            "<b>🏷️ Sosial Mühit — peşəkar bilik məkanı</b>\n"
            "━━━━━━━━━━━━\n"
            "• Pensiya indeksləri və kapital qaydaları\n"
            "• Müavinət məbləğləri, göstəricilər\n"
            "• Fərmanlar, qərarlar, dəyişikliklər\n\n"
            "<i>Fayl bazası + praktik nümunələr + sual-cavab — mütəmadi yenilənir.</i>"
        ),
    }
    return texts.get(key, "")

async def timed_delete(message, delay=20):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    if callback.message:
        await callback.message.answer("Aşağıdakı seçimlərdən birini seçin və bütün funksiyalara rahat giriş əldə edin:", reply_markup=get_main_buttons())
    await callback.answer()

@router.callback_query(F.data == "about_channels")
async def about_channels_callback(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sosial Mühit", callback_data="channel_sosial_muhit")],
            [InlineKeyboardButton(text="Burada sizin kanalınız ola bilərdi", callback_data="channel_empty1")],
            [InlineKeyboardButton(text="Burada sizin kanalınız ola bilərdi", callback_data="channel_empty2")]
        ]
    )
    if callback.message:
        msg = await callback.message.answer(get_text("about_channels_info"), reply_markup=keyboard)
        asyncio.create_task(timed_delete(msg))
    await callback.answer()

@router.callback_query(F.data == "channel_sosial_muhit")
async def channel_sosial_muhit_callback(callback: CallbackQuery, state: FSMContext):
    if callback.message:
        msg = await callback.message.answer(get_text("channel_sosial_muhit"), parse_mode="HTML")
        asyncio.create_task(timed_delete(msg))
    await callback.answer()

@router.callback_query(F.data == "main_action")
async def main_action_callback(callback: CallbackQuery, state: FSMContext):
    if callback.message is not None:
        await callback.message.answer("🏠 Əsas menyuya qayıtdınız.")
    await callback.answer()

@router.callback_query(F.data == "back")
async def back_callback(callback: CallbackQuery, state: FSMContext):
    if callback.message is not None:
        await callback.message.answer("🏠 Əsas menyuya qayıt:", reply_markup=main_menu_keyboard)
    await callback.answer()