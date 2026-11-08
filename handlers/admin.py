from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from config import ADMIN_ID
import datetime
from collections import Counter
from datetime import datetime, timedelta
from aiogram.filters import CommandObject
from utils.history_logger import get_user_history, summarize_user_history
from utils.timezone_utils import get_baku_time_str, get_baku_time_short, get_baku_time
from database.db import clear_all_data, get_all_user_activity

router = Router()

@router.message(Command(commands=["admin"]))
async def admin_panel(message: Message, state: FSMContext):
    if not message.from_user or message.from_user.id != ADMIN_ID:
        # provide short diagnostic to help configure ADMIN_ID if needed
        user_id = message.from_user.id if message.from_user else "unknown"
        await message.answer(
            f"Bu funksiya yalnız admin üçündür.\n"
            f"Sənin id: {user_id}\n"
            f"Konfiqdə ADMIN_ID: {ADMIN_ID}\n\n"
            f"Qeyd: Qrupda istifadə edirsinizsə, istifadəçi mesajı `/admin@BotUsername` şəklində gələ bilər; bu handler həm fərdi həm də qrupda işləyir."
        )
        return

    try:
        rows = get_all_user_activity()
        if not rows:
            await message.answer("Heç bir fəaliyyət qeydi yoxdur.")
            return

        users = set()
        actions = []
        langs = []
        # For top active users we count by username (fallback to id)
        user_activity_counter = Counter()
        # Track earliest seen date per user to compute new users in last 7 days
        earliest_seen = {}
        for row in rows:
            user_id = str(row["user_id"])
            username = row["username"] or ""
            action = row["action"] or ""
            date_str = row["occurred_at"]
            lang = row["language"] or "unknown"
            users.add(user_id)
            actions.append(action)
            langs.append(lang)

            who = username.strip() or user_id
            user_activity_counter[who] += 1

            # parse date with fallbacks
            parsed_date = None
            try:
                # try ISO first
                parsed_date = datetime.fromisoformat(date_str)
            except Exception:
                try:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    parsed_date = None

            if parsed_date is not None:
                if user_id not in earliest_seen or parsed_date < earliest_seen[user_id]:
                    earliest_seen[user_id] = parsed_date

        total_users = len(users)
        latest_activity = rows[-1]["occurred_at"]
        most_common_actions = Counter(actions).most_common(3)
        most_common_langs = Counter(langs).most_common(3)
        # Top 10 active users
        top_10_users = user_activity_counter.most_common(10)
        # New users in last 7 days (based on earliest_seen)
        cutoff = get_baku_time().replace(tzinfo=None) - timedelta(days=7)
        new_users_last_7 = sum(1 for d in earliest_seen.values() if d >= cutoff)

        text = (
            f"📊 <b>Admin Panel Hesabatı</b>\n"
            f"👥 Ümumi istifadəçilər: <b>{total_users}</b>\n"
            f"📅 Son qeyd: <i>{latest_activity}</i>\n\n"
            f"🔥 Ən çox əməl edilən fəaliyyətlər:\n"
        )

        for action, count in most_common_actions:
            text += f" — {action}: {count} dəfə\n"

        text += "\n"
        # include language breakdown
        text += "🌐 Ən çox istifadə olunan dillər:\n"
        for lang, count in most_common_langs:
            text += f" — {lang}: {count} dəfə\n"

        text += "\n"
        # Top 10 active users
        text += "👑 Top 10 ən aktiv istifadəçi:\n"
        if top_10_users:
            for i, (who, cnt) in enumerate(top_10_users, start=1):
                text += f" {i}. {who} — {cnt} əməliyyat\n"
        else:
            text += " Heç bir aktiv istifadəçi qeydə alınmayıb\n"

        text += "\n"
        text += f"🆕 Son 7 günə əlavə olunan yeni istifadəçilər: <b>{new_users_last_7}</b>\n"

        # send report to admin
        await message.answer(text, parse_mode="HTML")
        return
    except Exception as e:
        await message.answer(f"Fəaliyyət qeydləri oxunarkən xəta baş verdi: {e}")
        return


@router.message(Command("clearall"))
async def clear_all_command(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_ID:
        await message.answer("Bu əmr yalnız admin üçündür.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Təsdiqlə", callback_data="clearall_confirm"),
                InlineKeyboardButton(text="Ləğv et", callback_data="clearall_cancel"),
            ]
        ]
    )
    await message.answer(
        "⚠️ Bu əməliyyat bütün istifadəçi məlumatlarını, balansları, tarixçələri, xəbərləri və sifarişləri siləcək.\n"
        "Bu əməliyyatı geri qaytarmaq mümkün deyil. Davam etmək istəyirsiniz?",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "clearall_confirm")
async def clear_all_confirm(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Bu əməliyyat yalnız admin üçündür.", show_alert=True)
        return

    try:
        tables = clear_all_data()
    except Exception:
        await callback.answer("Təmizləmə uğursuz oldu.", show_alert=True)
        if callback.message:
            await callback.message.answer("Verilənlər bazasını təmizləmək mümkün olmadı. Bağlantını yoxlayın.")
        return

    await callback.answer("Verilənlər bazası təmizləndi.")
    if callback.message:
        if tables:
            await callback.message.answer(
                f"✅ {len(tables)} cədvəlin məlumatı silindi. Miqrasiya qeydləri köhnə məlumatların yenidən yüklənməməsi üçün saxlanıldı."
            )
        else:
            await callback.message.answer("Təmizlənəcək məlumat cədvəli tapılmadı.")


@router.callback_query(F.data == "clearall_cancel")
async def clear_all_cancel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Bu əməliyyat yalnız admin üçündür.", show_alert=True)
        return
    await callback.answer("Təmizləmə ləğv edildi.")


@router.message(Command(commands=["history"]))
async def user_history_command(message: Message, command: CommandObject):
    """Admin-only: show RBCron balance history for a specific user id.

    Usage: /history <telegram_user_id>
    """
    if not message.from_user or message.from_user.id != ADMIN_ID:
        await message.answer("Bu funksiya yalnız admin üçündür.")
        return

    arg = (command.args or "").strip()
    if not arg or not arg.isdigit():
        await message.answer("İstifadə: /history <telegram_user_id>")
        return

    uid = int(arg)
    events = get_user_history(uid)
    summary = summarize_user_history(uid)

    if not events:
        await message.answer(f"🧾 İstifadəçi {uid} üçün heç bir balans əməliyyatı qeydi yoxdur.")
        return

    # Build summary
    text = (
        f"🧾 <b>RBCron tarixçə</b> — <code>{uid}</code>\n"
        f"Qeyd sayı: <b>{summary['count']}</b>\n"
        f"Toplam artırılan: <b>{summary['total_topup']}</b>\n"
        f"Toplam xərclənən: <b>{summary['total_spent']}</b>\n"
        f"İlk qeyd: {summary['first_ts'] or '-'}\n"
        f"Son qeyd: {summary['last_ts'] or '-'}\n\n"
        f"Son 20 əməliyyat:\n"
    )

    # Show last 20 events
    for e in events[-20:]:
        ts = e.get("ts")
        delta = e.get("delta")
        prev_v = e.get("prev")
        new_v = e.get("new")
        reason = e.get("reason") or "-"
        source = e.get("source") or "-"
        sign = "+" if delta and delta > 0 else ""
        text += f"• {ts} — {sign}{delta} ( {prev_v} → {new_v} )  [{source}]  reason: {reason}\n"

    await message.answer(text, parse_mode="HTML")


# Admin üçün kanal məlumatları əldə etmə
@router.message(F.text.in_(["get_channel_info", "ping", "/get_channel_info", "/ping"]))
async def get_channel_info_command(message: Message):
    """Admin qrupda ping və ya get_channel_info yazanda kanal məlumatlarını göstər"""
    # Yalnız admin istifadə edə bilər
    if not message.from_user or message.from_user.id != ADMIN_ID:
        return  # Sessizlik - admin deyilsə cavab vermirik
    
    try:
        chat = message.chat
        
        # Chat məlumatlarını topla
        chat_info = {
            "chat_id": chat.id,
            "type": chat.type,
            "title": getattr(chat, 'title', 'N/A'),
            "username": getattr(chat, 'username', None),
            "description": getattr(chat, 'description', None),
        }
        
        # Bot admin statusunu yoxla
        try:
            bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)
            bot_status = bot_member.status
            bot_permissions = getattr(bot_member, 'can_delete_messages', False)
        except Exception:
            bot_status = "unknown"
            bot_permissions = False
        
        # Chat üzv sayını al (əgər mümkündürsə)
        try:
            member_count = await message.bot.get_chat_member_count(chat.id)
        except Exception:
            member_count = "N/A"
        
        # Cavab mətnini hazırla
        response_text = (
            f"🏷️ <b>Kanal/Qrup Məlumatları</b>\n\n"
            f"🆔 <b>Chat ID:</b> <code>{chat_info['chat_id']}</code>\n"
            f"📝 <b>Ad:</b> {chat_info['title']}\n"
            f"📂 <b>Növ:</b> {chat_info['type']}\n"
        )
        
        if chat_info['username']:
            response_text += f"🔗 <b>Username:</b> @{chat_info['username']}\n"
            
        if chat_info['description']:
            desc_short = chat_info['description'][:100] + "..." if len(chat_info['description']) > 100 else chat_info['description']
            response_text += f"📄 <b>Təsvir:</b> {desc_short}\n"
        
        response_text += (
            f"👥 <b>Üzv sayı:</b> {member_count}\n"
            f"🤖 <b>Bot statusu:</b> {bot_status}\n"
            f"⚙️ <b>Admin hüquqları:</b> {'✅' if bot_permissions else '❌'}\n\n"
            f"🕐 <b>Vaxt (Bakı):</b> {get_baku_time_str()}"
        )
        
        await message.reply(response_text, parse_mode="HTML")
        
    except Exception as e:
        await message.reply(f"❌ Məlumat əldə edilərkən xəta: {str(e)}")


# Qısa ping cavabı
@router.message(F.text.in_(["ping!", "pong", "/pong"]))
async def ping_response(message: Message):
    """Admin ping yazanda qısa cavab"""
    if not message.from_user or message.from_user.id != ADMIN_ID:
        return
    
    await message.reply(
        f"🏓 Pong!\n"
        f"Chat ID: <code>{message.chat.id}</code>\n"
        f"Vaxt (Bakı): {get_baku_time_short()}", 
        parse_mode="HTML"
    )
