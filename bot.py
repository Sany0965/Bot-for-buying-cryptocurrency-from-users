import threading
import time
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, InputMediaPhoto
import config
import db
import payments

db.create_table()
bot = telebot.TeleBot(config.TELEGRAM_TOKEN, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def handle_start(message):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('🚀 Начать обмен', callback_data='ask_amount'))
    bot.send_message(
        message.chat.id,
        '👋 *Здравствуйте!*\nВы здесь чтобы обналичить криптовалюту.\nНажмите кнопку ниже, чтобы приступить.',
        reply_markup=kb
    )

@bot.message_handler(commands=['help'])
def handle_help(message):
    text = (
        'ℹ️ *Добро пожаловать в наш бот!*\n\n'
        'Вот что он умеет:\n'
        '• Принимает криптовалюту *через Cryptobot* (можно пополнить из сторонних кошельков и обменять у нас)\n'
        '• Мгновенный вывод средств на карту (*кошелёк YooMoney должен быть подтверждён*)\n'
        '• Возврат средств при отмене операции\n\n'
        '📌 *Как это происходит:*\n'
        '1. Вы указываете сумму в USDT\n'
        '2. Вводите номер счёта *YooMoney*\n'
        '3. Оплачиваете счёт криптовалютой\n'
        '4. Подтверждаете отправку средств\n'
        '5. Если передумали - используйте кнопку "Нет, вернуть" для отмены\n\n'
        '✅ Всё готово! Чек для возврата придет автоматически.\n\n'
        '_Смотрите примеры на фото выше_\n\n'
        '🤖 Бот создан: @worpli'
    )
    media_group = [
        InputMediaPhoto(open('1.jpg', 'rb'), caption=text, parse_mode='Markdown'),
        InputMediaPhoto(open('2.jpg', 'rb'))
    ]
    bot.send_media_group(message.chat.id, media_group)

@bot.callback_query_handler(func=lambda call: call.data == 'ask_amount')
def ask_amount(call):
    bot.send_message(call.message.chat.id, '💰 *Введите сумму* _USDT_ для обмена (минимум 0.1 USDT):')
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_amount)

def process_amount(message):
    chat_id = message.chat.id
    try:
        amount = float(message.text.replace(',', '.'))
        if amount < 0.1:
            raise ValueError()
    except:
        bot.send_message(chat_id, '❌ Неверная сумма. Попробуйте ещё раз:')
        bot.register_next_step_handler_by_chat_id(chat_id, process_amount)
        return
    db.save_amount(chat_id, amount)
    bot.send_message(chat_id, '📞 *Введите номер счёта YooMoney* для получения денег:')
    bot.register_next_step_handler_by_chat_id(chat_id, process_phone)

def process_phone(message):
    chat_id = message.chat.id
    phone = message.text.strip().replace(" ", "")  
    
    
    error_msg = None
    if not phone.isdigit():
        error_msg = "❌ Номер счета должен содержать только цифры"
    elif len(phone) != 16:
        error_msg = "❌ Номер счета должен содержать 16 цифр"
    elif not phone.startswith('4100'):
        error_msg = "❌ Номер счета должен начинаться с 4100"
    
    if error_msg:
        bot.send_message(chat_id, f"{error_msg}!\nПопробуйте еще раз:")
        bot.register_next_step_handler_by_chat_id(chat_id, process_phone)
        return
    
    db.save_phone(chat_id, phone)
    data = db.get_user(chat_id)
    amount = data[1]
    pay_url, invoice_id = payments.create_invoice(amount)
    db.save_invoice(chat_id, invoice_id)
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('💳 Оплатить счёт', url=pay_url))
    msg = bot.send_message(chat_id, f'🔗 Ссылка на оплату *{amount:.2f} USDT*:\nНажмите кнопку ниже.', reply_markup=kb)
    db.save_msg_id(chat_id, msg.message_id)
    threading.Thread(target=wait_for_payment, args=(chat_id,)).start()

def wait_for_payment(chat_id):
    invoice_id = db.get_user(chat_id)[3]
    while True:
        status = payments.check_invoice_paid(invoice_id)
        print(f"Проверка статуса: {status}")
        if status == 'paid':
            try:
                msg_id = db.get_user(chat_id)[8]
                bot.delete_message(chat_id, msg_id)
            except:
                pass
            send_result_by_chat_id(chat_id)
            break
        time.sleep(2)

def send_result_by_chat_id(chat_id):
    data = db.get_user(chat_id)
    amount = data[1]
    phone = data[2]
    rate = payments.get_usdt_to_rub_rate()
    rub = amount * rate
    commission = rub * 0.05
    total = rub - commission
    db.save_final(chat_id, rate, rub, commission, total)

    text = (
        '📊 *Данные обмена:*\n'
        f'• Вы меняете: *{amount:.2f} USDT*\n'
        f'• Курс: *{rate:.2f} RUB/USDT*\n'
        f'• Получаете до комиссии: *{rub:.2f} ₽*\n'
        f'• Комиссия (5%): *{commission:.2f} ₽*\n'
        f'• Итого к выплате:(не считая комиссии yoomoney) *{total:.2f} ₽*\n\n'
        '📱 *Реквизиты:*\n'
        f'Номер счета: *{phone}*\n\n'
        'Выполнить отправку средств?Данное сообщение будет удалено через 5 минут'
    )
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton('✅ Да, отправить', callback_data='confirm_send'),
        InlineKeyboardButton('❌ Нет, вернуть', callback_data='cancel_send')
    )
    msg = bot.send_message(chat_id, text, reply_markup=kb)
    time.sleep(300)
    try:
        bot.delete_message(chat_id, msg.message_id)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_send')
def confirm_and_send(call):
    chat_id = call.message.chat.id
    data = db.get_user(chat_id)
    phone = data[2]
    total_rub = data[7]
    payments.send_yoomoney_payment(phone, total_rub, 'Обмен крипты бот')
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    bot.send_message(chat_id, '🎉 *Деньги успешно отправлены!*\nСпасибо за обращение. Бот создал https://t.me/worpli')

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_send')
def handle_cancel_send(call):
    chat_id = call.message.chat.id
    data = db.get_user(chat_id)
    amount = data[1]
    
    try:
        check_response = payments.create_crypto_check(chat_id, amount)
        
        if check_response and check_response.get('result'):
            bot.send_message(
                chat_id,
                f"♻️ *Возврат оформлен!*\n\n"
                f"Чек на *{amount:.2f} USDT*:\n"
                f"{check_response['result']['bot_check_url']}\n\n"
                "Ссылка действительна 24 часа."
            )
            db.delete_user(chat_id)
        else:
            error = check_response.get('error', 'Неизвестная ошибка') if check_response else 'Нет ответа от API'
            bot.send_message(
                chat_id,
                f"❌ *Ошибка возврата*: {error}\nОбратитесь в поддержку @support"
            )
            
    except Exception as e:
        bot.send_message(chat_id, "⚠️ Произошла внутренняя ошибка при обработке запроса")
        print(f"Ошибка возврата: {str(e)}")
    
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass

if __name__ == '__main__':
    bot.polling(none_stop=True)