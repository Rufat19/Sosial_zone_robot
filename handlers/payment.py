import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from config import ADMIN_ID, PAYMENT_CURRENCY, PAYMENT_PROVIDER_TOKEN
from database.db import credit_telegram_payment

payment_router = Router()
logger = logging.getLogger(__name__)

PAYMENT_PACKAGES = {
    "5": (Decimal("5.00"), 500),
    "20": (Decimal("20.00"), 1000),
    "50": (Decimal("50.00"), 2000),
}


def _get_payment_details(payload: str):
    parts = payload.split(":")
    if len(parts) != 3 or parts[0] != "rbcron":
        return None
    try:
        user_id = int(parts[1])
    except ValueError:
        return None
    package = PAYMENT_PACKAGES.get(parts[2])
    if package is None:
        return None
    return user_id, package


@payment_router.callback_query(F.data.startswith("buy_rbc_"))
async def create_balance_invoice(callback: CallbackQuery):
    if not PAYMENT_PROVIDER_TOKEN:
        await callback.answer("Telegram ödəniş provayderi qurulmayıb.", show_alert=True)
        return
    if callback.message is None or callback.data is None:
        await callback.answer("Ödəniş sorğusu oxunmadı.", show_alert=True)
        return

    package_id = callback.data.rsplit("_", 1)[-1]
    package = PAYMENT_PACKAGES.get(package_id)
    if package is None:
        await callback.answer("Seçilmiş paket tapılmadı.", show_alert=True)
        return

    rbcron_amount, price_minor_units = package
    await callback.answer()
    await callback.message.answer_invoice(
        title=f"{rbcron_amount:g} RBCron",
        description=f"{rbcron_amount:g} RBCron balansınıza əlavə olunacaq.",
        payload=f"rbcron:{callback.from_user.id}:{package_id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=PAYMENT_CURRENCY,
        prices=[LabeledPrice(label=f"{rbcron_amount:g} RBCron", amount=price_minor_units)],
    )


@payment_router.pre_checkout_query()
async def confirm_pre_checkout(query: PreCheckoutQuery):
    details = _get_payment_details(query.invoice_payload)
    if details is None:
        await query.answer(ok=False, error_message="Ödəniş paketi etibarlı deyil.")
        return

    user_id, (rbcron_amount, price_minor_units) = details
    if (
        query.from_user.id != user_id
        or query.currency != PAYMENT_CURRENCY
        or query.total_amount != price_minor_units
    ):
        await query.answer(ok=False, error_message="Ödəniş məlumatları uyğun gəlmir.")
        return

    await query.answer(ok=True)


@payment_router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payment = message.successful_payment
    user = message.from_user
    details = _get_payment_details(payment.invoice_payload)

    if user is None or details is None:
        logger.error("Telegram ödənişinin payload məlumatı etibarsızdır.")
        await message.answer("Ödəniş alındı, amma paket müəyyən edilmədi. Adminə müraciət edin.")
        return

    expected_user_id, (rbcron_amount, expected_total) = details
    if (
        user.id != expected_user_id
        or payment.currency != PAYMENT_CURRENCY
        or payment.total_amount != expected_total
    ):
        logger.error("Telegram ödənişinin istifadəçi və ya məbləğ məlumatı uyğun gəlmir.")
        await message.answer("Ödəniş məlumatları təsdiqlənmədi. Adminə müraciət edin.")
        return

    try:
        new_balance = credit_telegram_payment(
            telegram_charge_id=payment.telegram_payment_charge_id,
            provider_charge_id=payment.provider_payment_charge_id,
            user_id=user.id,
            currency=payment.currency,
            total_amount=payment.total_amount,
            rbcron_amount=rbcron_amount,
        )
    except Exception:
        logger.exception("Uğurlu Telegram ödənişindən sonra balansı artırmaq alınmadı.")
        if ADMIN_ID:
            try:
                await message.bot.send_message(
                    ADMIN_ID,
                    f"Balansı avtomatik artırmaq alınmadı. İstifadəçi: {user.id}; "
                    f"Telegram ödəniş ID-si: {payment.telegram_payment_charge_id}",
                )
            except Exception:
                logger.exception("Ödəniş xətası barədə adminə bildirmək alınmadı.")
        await message.answer("Ödəniş təsdiqləndi, balansın yazılması yoxlanılır. Zəhmət olmasa gözləyin.")
        return

    if new_balance is None:
        await message.answer("Bu ödəniş artıq balansa əlavə olunub.")
        return

    await message.answer(
        f"✅ Ödəniş uğurla tamamlandı. Balansınıza {rbcron_amount:g} RBCron əlavə edildi.\n"
        f"Yeni balansınız: {new_balance:.2f} RBCron"
    )
