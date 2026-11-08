# handlers/news_handler.py
from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import ADMIN_ID
from database import add_news_to_db, get_all_news, get_news_by_id, get_all_users

router = Router()

# Lokal ehtiyat yaddaş (PostgreSQL işləməsə belə)
local_news_cache = []


# FSM mərhələləri
class AddNewsState(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()


# 🔹 Admin "Yenilik əlavə et" əmri ilə prosesi başladır
@router.message(Command("add_news"))
async def start_add_news(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Bu əmri yalnız admin yaza bilər.")
    
    await message.answer("📝 Yeni yenilik əlavə et — əvvəlcə başlığı yazın:")
    await state.set_state(AddNewsState.waiting_for_title)


# 🔹 Başlıq daxil edilir
@router.message(AddNewsState.waiting_for_title)
async def get_news_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📄 İndi isə yeniliyin məzmununu yaz (qısa və aydın):")
    await state.set_state(AddNewsState.waiting_for_content)


# 🔹 Məzmun daxil edilir və DB-yə yazılır
@router.message(AddNewsState.waiting_for_content)
async def save_news_content(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data["title"]
    content = message.text

    # DB-yə yazmağa cəhd
    try:
        news_id = add_news_to_db(title, content, message.from_user.id)
        if not news_id:
            # Əgər DB cavab vermirsə, lokal yaddaşa yaz
            news_id = len(local_news_cache) + 1
            local_news_cache.append({
                "id": news_id,
                "title": title,
                "content": content
            })
    except Exception as e:
        news_id = len(local_news_cache) + 1
        local_news_cache.append({
            "id": news_id,
            "title": title,
            "content": content
        })

    await state.clear()

    # Bütün istifadəçilərə göndəririk
    try:
        users = get_all_users()
    except Exception:
        users = []  # əgər DB işləməsə, heç kimə göndərmirik

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Ətraflı oxu", callback_data=f"read_news:{news_id}")]
        ]
    )

    for user in users:
        user_id = user.get("user_id") or user.get("id")
        if not user_id:
            continue
        try:
            # göndəriləcək mesaj daha canlı olsun — başlıq + qısa xəbər
            await message.bot.send_message(
                chat_id=user_id,
                text=f"📢 *{title}*\n\n{content[:200]}...\n\n🔔 Yeniliyi tam oxumaq üçün düyməyə basın.",
                reply_markup=kb,
                parse_mode="Markdown"
            )
        except Exception:
            continue  # bəziləri block edə bilər, davam et

    await message.answer("✨ Uğurla əlavə olundu və istifadəçilərə göndərildi.")


# 🔹 Xəbəri oxumaq üçün inline düymə
@router.callback_query(F.data.startswith("read_news:"))
async def read_news_cb(query: CallbackQuery):
    news_id = int(query.data.split(":")[1])
    try:
        news = get_news_by_id(news_id)
    except Exception:
        news = next((n for n in local_news_cache if n["id"] == news_id), None)

    if not news:
        return await query.answer("❌ Xəbər tapılmadı.", show_alert=True)
    await query.message.answer(
        f"📌 <b>{news['title']}</b>\n\n{news['content']}",
        parse_mode="HTML"
    )
    await query.answer()


# 🔹 İnvestisiya xəbərləri komandası
@router.message(Command("news"))
async def list_news(message: Message):
    try:
        news_list = get_all_news()
    except Exception:
        news_list = local_news_cache

    if not news_list:
        return await message.answer("📭 Hələlik investisiya xəbəri yoxdur.")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=n["title"], callback_data=f"read_news:{n['id']}")] for n in news_list
    ])
    await message.answer("📈 İnvestisiya xəbərləri — seçin:", reply_markup=kb)


# 🔹 İnvestisiya xəbərlərinin inline düyməsi
@router.callback_query(F.data == "show_news")
async def show_news_from_inline(query: CallbackQuery):
    try:
        news_list = get_all_news()
    except Exception:
        news_list = local_news_cache

    if not news_list:
        return await query.answer("📭 Hələlik investisiya xəbəri yoxdur.", show_alert=True)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=n["title"], callback_data=f"read_news:{n['id']}")] for n in news_list
    ])
    await query.message.answer("📈 İnvestisiya xəbərləri:", reply_markup=kb)
    await query.answer()
