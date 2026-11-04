import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_db_connection
from handlers.balance_utils import deduct_balance
from handlers.db_utils import get_balance

router = Router()

EXCEL_LESSONS_DIR = "excel_lessons"
EXCEL_ACCESS_PRICE = 1500

# FSM states for registration
class ExcelRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

# Helper functions for database
def has_excel_access(user_id):
    """Check if user has paid for Excel lessons access."""
    with get_db_connection() as conn:
        row = conn.execute("SELECT access_granted FROM excel_access WHERE user_id = %s", (user_id,)).fetchone()
        return row is not None and row["access_granted"]

def grant_excel_access(user_id, full_name, phone):
    """Grant Excel lessons access to user after payment."""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO excel_access (user_id, full_name, phone, access_granted)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (user_id) DO UPDATE
            SET full_name=EXCLUDED.full_name, phone=EXCLUDED.phone, access_granted=TRUE
        """, (user_id, full_name, phone))
        conn.commit()

# Main menu for Excel lessons - check access first
@router.callback_query(F.data == "excel_lessons_menu")
async def excel_lessons_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Check if user already has access
    if has_excel_access(user_id):
        await show_folders_menu(callback)
    else:
        # Show payment info and ask for confirmation
        user_balance = get_balance(user_id)
        
        info_text = (
            "📊 <b>Excel Dərsləri - Giriş</b>\n\n"
            "Bu bölmədə Excel öyrənmək üçün dərs materialları mövcuddur.\n\n"
            f"💰 <b>Qiymət:</b> {EXCEL_ACCESS_PRICE} RBCron\n"
            f"💳 <b>Sizin balansınız:</b> {user_balance} RBCron\n\n"
            "Ödənişdən sonra bütün Excel dərs materiallarına ömürlük giriş əldə edəcəksiniz.\n\n"
            "Davam etmək istəyirsiniz?"
        )
        
        keyboard = []
        if user_balance >= EXCEL_ACCESS_PRICE:
            keyboard.append([InlineKeyboardButton(text="✅ Bəli, ödəniş et", callback_data="excel_confirm_payment")])
        else:
            keyboard.append([InlineKeyboardButton(text="💰 Balans artır", callback_data="balance_menu")])
        
        keyboard.append([InlineKeyboardButton(text="❌ Ləğv et", callback_data="main_menu")])
        
        await callback.message.edit_text(info_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    await callback.answer()

# Confirm payment and start registration
@router.callback_query(F.data == "excel_confirm_payment")
async def confirm_excel_payment(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_balance = get_balance(user_id)
    
    if user_balance < EXCEL_ACCESS_PRICE:
        await callback.message.answer("❌ Balansınız kifayət deyil. Zəhmət olmasa balansınızı artırın.")
        await callback.answer()
        return
    
    # Start registration process
    await callback.message.edit_text(
        "📝 <b>Qeydiyyat</b>\n\n"
        "Zəhmət olmasa <b>Ad və Soyadınızı</b> daxil edin:",
        parse_mode="HTML"
    )
    await state.set_state(ExcelRegistration.waiting_for_name)
    await callback.answer()

# Handle name input
@router.message(ExcelRegistration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    
    if len(full_name) < 3:
        await message.answer("❌ Zəhmət olmasa düzgün ad və soyad daxil edin (ən azı 3 simvol).")
        return
    
    await state.update_data(full_name=full_name)
    await message.answer(
        "📱 İndi <b>mobil nömrənizi</b> daxil edin:\n"
        "(Məsələn: +994501234567)",
        parse_mode="HTML"
    )
    await state.set_state(ExcelRegistration.waiting_for_phone)

# Handle phone input and complete payment
@router.message(ExcelRegistration.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    
    if len(phone) < 9:
        await message.answer("❌ Zəhmət olmasa düzgün mobil nömrə daxil edin.")
        return
    
    user_id = message.from_user.id
    data = await state.get_data()
    full_name = data.get("full_name")
    
    # Deduct balance
    if deduct_balance(user_id, EXCEL_ACCESS_PRICE):
        # Grant access
        grant_excel_access(user_id, full_name, phone)
        
        # Clear state first
        await state.clear()
        
        await message.answer(
            f"✅ <b>Təbriklər!</b>\n\n"
            f"Ödəniş uğurla tamamlandı ({EXCEL_ACCESS_PRICE} RBCron tutuldu).\n"
            f"İndi Excel dərs materiallarına tam giriş hüququnuz var!",
            parse_mode="HTML"
        )
        
        # Show folders directly
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Excel lessons dir: {EXCEL_LESSONS_DIR}")
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(f"Excel dir exists: {os.path.exists(EXCEL_LESSONS_DIR)}")
            
            if not os.path.exists(EXCEL_LESSONS_DIR):
                await message.answer(f"❌ Dərslik qovluğu tapılmadı: {EXCEL_LESSONS_DIR}\nZəhmət olmasa adminlə əlaqə saxlayın.")
                return
                
            folders = [d for d in os.listdir(EXCEL_LESSONS_DIR) if os.path.isdir(os.path.join(EXCEL_LESSONS_DIR, d))]
            folders.sort()
            
            logger.info(f"Found {len(folders)} folders: {folders}")

            if not folders:
                await message.answer("⚠️ Hazırda heç bir dərs materialı yoxdur.")
                return

            keyboard = []
            for folder in folders:
                keyboard.append([InlineKeyboardButton(text=f"📁 {folder}", callback_data=f"list_files:{folder}")])
            
            keyboard.append([InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")])

            await message.answer(
                "📚 Zəhmət olmasa, bir dərs qovluğu seçin:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error showing folders: {e}", exc_info=True)
            await message.answer(f"❌ Xəta baş verdi: {e}\nZəhmət olmasa adminlə əlaqə saxlayın.")
    else:
        await message.answer("❌ Balansınız kifayət deyil. Zəhmət olmasa balansınızı artırın.")
        await state.clear()

# Show folders after access is granted
@router.callback_query(F.data == "excel_show_folders")
async def show_folders_callback(callback: CallbackQuery):
    if has_excel_access(callback.from_user.id):
        await show_folders_menu(callback)
    else:
        await callback.message.answer("❌ Sizin Excel dərslərinə giriş hüququnuz yoxdur.")
    await callback.answer()

async def show_folders_menu(callback: CallbackQuery):
    """Display available lesson folders."""
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"show_folders_menu called - Excel dir: {EXCEL_LESSONS_DIR}, exists: {os.path.exists(EXCEL_LESSONS_DIR)}")
        
        if not os.path.exists(EXCEL_LESSONS_DIR):
            await callback.message.edit_text(f"❌ Dərslik qovluğu tapılmadı: {EXCEL_LESSONS_DIR}")
            return
            
        folders = [d for d in os.listdir(EXCEL_LESSONS_DIR) if os.path.isdir(os.path.join(EXCEL_LESSONS_DIR, d))]
        folders.sort()
        
        logger.info(f"Found folders: {folders}")

        if not folders:
            await callback.message.edit_text("⚠️ Hazırda heç bir dərs materialı yoxdur.")
            return

        keyboard = []
        for folder in folders:
            keyboard.append([InlineKeyboardButton(text=f"📁 {folder}", callback_data=f"list_files:{folder}")])
        
        keyboard.append([InlineKeyboardButton(text="🏠 Əsas menyuya qayıt", callback_data="main_menu")])

        await callback.message.edit_text(
            "📚 Zəhmət olmasa, bir dərs qovluğu seçin:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in show_folders_menu: {e}", exc_info=True)
        await callback.message.edit_text(f"❌ Xəta: {e}")

# List files in a selected folder
@router.callback_query(F.data.startswith("list_files:"))
async def list_lesson_files(callback: CallbackQuery):
    # Check access
    if not has_excel_access(callback.from_user.id):
        await callback.message.answer("❌ Sizin Excel dərslərinə giriş hüququnuz yoxdur.")
        await callback.answer()
        return
    
    folder_name = callback.data.split(":", 1)[1]
    folder_path = os.path.join(EXCEL_LESSONS_DIR, folder_name)

    try:
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        
        if not files:
            await callback.message.answer(f"⚠️ '{folder_name}' qovluğunda heç bir fayl tapılmadı.")
            await callback.answer()
            return

        keyboard = []
        for file in files:
            keyboard.append([InlineKeyboardButton(text=f"📄 {file}", callback_data=f"send_file:{folder_name}:{file}")])
        
        keyboard.append([InlineKeyboardButton(text="⬅️ Geri", callback_data="excel_show_folders")])

        await callback.message.edit_text(f"'{folder_name}' qovluğundakı fayllar:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

    except FileNotFoundError:
        await callback.message.answer("❌ Qovluq tapılmadı.")
    
    await callback.answer()

# Send the selected file
@router.callback_query(F.data.startswith("send_file:"))
async def send_lesson_file(callback: CallbackQuery):
    # Check access
    if not has_excel_access(callback.from_user.id):
        await callback.message.answer("❌ Sizin Excel dərslərinə giriş hüququnuz yoxdur.")
        await callback.answer()
        return
    
    try:
        _, folder_name, file_name = callback.data.split(":", 2)
        file_path = os.path.join(EXCEL_LESSONS_DIR, folder_name, file_name)

        if os.path.exists(file_path):
            document = FSInputFile(file_path)
            await callback.message.answer_document(document, caption=f"Buyurun, '{file_name}' faylı.")
        else:
            await callback.message.answer("❌ Fayl tapılmadı.")
            
    except Exception as e:
        await callback.message.answer(f"❗️ Fayl göndərilərkən xəta baş verdi: {e}")

    await callback.answer()

