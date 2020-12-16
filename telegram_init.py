import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    CallbackQueryHandler, ConversationHandler

# initialize response list
from py_func import greet, unknown, conv_end
from py_func.bbi_info import bbi_start, bbi_callback_handler, ROUTE, DEST, SEC_ROUTE

# Enable logging
from py_func.reminder import date_counter

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

# Bot Credential
updater = Updater('1460342157:AAH26oIP5bwvL6SMgx3lE4BsiQLnAiidGQ8', use_context=True)


# def counter(update, context):
#     """/start"""
#     context.bot.send_message(chat_id=update.effective_chat.id, text='Hi BB, this is our AI reminder')
#     # updater.job_queue.run_repeating(date_counter, context=update.effective_chat.id, interval=86400,  first=0.1)

if __name__ == '__main__':
    """add functions to dispatcher"""
    dp = updater.dispatcher

    """Greeting"""
    dp.add_handler(CommandHandler('hi', greet))

    """Date Counter"""
    dp.add_handler(CommandHandler('counter', date_counter))

    """BBI flow"""
    bbi_handler = ConversationHandler(
        entry_points=[CommandHandler('bbi', bbi_start)],
        states={
            ROUTE: [MessageHandler(Filters.regex('^\w?[0-9]+\w?$'), bbi_callback_handler)],
            DEST: [CallbackQueryHandler(bbi_callback_handler)],
            SEC_ROUTE: [CallbackQueryHandler(bbi_callback_handler)]
        },
        fallbacks=[CommandHandler('end', conv_end)]
    )
    dp.add_handler(bbi_handler)

    # dp.add_handler(CommandHandler('dating', date_counter, pass_job_queue=True))

    """Unknown handler"""
    dp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
