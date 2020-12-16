import argparse
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    CallbackQueryHandler, ConversationHandler

from py_func import greet, unknown, conv_end
from py_func.bbi_info import bbi_start, bbi_callback_handler, ROUTE, DEST, SEC_ROUTE
from py_func.counter import date_counter

# get environment vars
parser = argparse.ArgumentParser()
parser.add_argument("--botkey", help='Key from bot father')
args = parser.parse_args()

# Bot Credential
updater = Updater(args.botkey, use_context=True)

if __name__ == '__main__':

    # Define /bbi handler workflow
    bbi_handler = ConversationHandler(
        entry_points=[CommandHandler('bbi', bbi_start)],
        states={
            ROUTE: [MessageHandler(Filters.regex('^\w?[0-9]+\w?$'), bbi_callback_handler)],
            DEST: [CallbackQueryHandler(bbi_callback_handler)],
            SEC_ROUTE: [CallbackQueryHandler(bbi_callback_handler)]
        },
        fallbacks=[CommandHandler('end', conv_end)]
    )

    dp = updater.dispatcher
    # /hi
    dp.add_handler(CommandHandler('hi', greet))
    # /counter
    dp.add_handler(CommandHandler('counter', date_counter))
    # /bbi
    dp.add_handler(bbi_handler)
    # error handler
    dp.add_handler(MessageHandler(Filters.command, unknown))
    # dp.add_handler(CommandHandler('dating', date_counter, pass_job_queue=True))

    updater.start_polling()
