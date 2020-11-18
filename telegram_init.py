from uuid import uuid4
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from bbi_info import get_bbi_info


def start(update, context):
    """/start"""
    context.bot.send_message(chat_id=update.effective_chat.id, text="hey bb, try my breast!")


def put(update, context):
    """Usage: /put value"""
    # Generate ID and seperate value from command
    key = str(uuid4())
    # We don't use context.args here, because the value may contain whitespaces
    value = update.message.text.partition(' ')[2]

    # Store value
    context.user_data[key] = value

    update.message.reply_text(key)


def get(update, context):
    """Usage: /get uuid"""
    # Seperate ID from command
    key = context.args[0]

    # Load value
    value = context.user_data.get(key, 'Not found')
    update.message.reply_text(value)


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{update.message.text}")


def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def bbi(update, context):
    route = context.args[0]
    direction = context.args[1]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=get_bbi_info(route, direction)
                             )


if __name__ == '__main__':

    updater = Updater('1460342157:AAH26oIP5bwvL6SMgx3lE4BsiQLnAiidGQ8', use_context=True)

    """add functions to dispatcher"""
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('put', put))
    dp.add_handler(CommandHandler('get', get))
    dp.add_handler(CommandHandler('caps', caps))
    dp.add_handler(CommandHandler('bbi', bbi))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    """Unknown handler"""
    dp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
