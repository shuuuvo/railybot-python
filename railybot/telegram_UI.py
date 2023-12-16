import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, callbackcontext, Filters
from main import ChatBot

token = ''

# BOT DEFINITION

bot = telegram.Bot(token=token)
chatbot = ChatBot()

CONV_TAG, CONV_UPDATE = range(2)

# MESSAGES

welcome_message = 'Hi {}, I am RailyBot. How can I help you?'
cancel_message = 'Good bye {}'


# METHODS

def start(update, context=callbackcontext):
    user = update.message.from_user['first_name'] + ' ' + update.message.from_user['last_name']
    update.message.reply_text(welcome_message.format(user))
    return CONV_TAG


def get_tag(update, context):
    text = update.message.text
    if text == '/cancel':
        update.message.reply_text('Bye Bye!')
        return ConversationHandler.END

    text_return = chatbot.get_label(text)
    update.message.reply_text(text_return)
    if 'Can you tell me more' == text_return or 'This fixture will be available soon' == text_return:
        return CONV_TAG
    else:
        return CONV_UPDATE


def update_conv(update, context):
    text = update.message.text
    if text == '/cancel':
        update.message.reply_text('Bye Bye!')
        return ConversationHandler.END
    else:
        if chatbot.conv_type in ['shop','delay']:
            end_conv, reply = chatbot.conv_classes[chatbot.conv_type].conv_update(text)
            update.message.reply_text(reply)
            if end_conv:
                return ConversationHandler.END

    return CONV_UPDATE


def main():
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CONV_TAG: [MessageHandler(Filters.text, get_tag)],
            CONV_UPDATE: [MessageHandler(Filters.text, update_conv)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()


def cancel(update, context):
    user_id = update.message.from_user['id']
    update.message.reply_text(cancel_message.format(user_id))
    return ConversationHandler.END


if __name__ == '__main__':
    main()
