import argparse

from telegram.ext import \
    CallbackQueryHandler, CommandHandler, ConversationHandler, Filters, \
    MessageHandler, Updater

from py_func import conv_end, greet, unknown
from py_func.bbi_info import \
    DEST, ROUTE, SEC_ROUTE, \
    bbi_callback_handler, bbi_start
from py_func.counter import \
    date_counter, add_dates_handler, remove_dates_handler, \
    SHOW_DATE, ADD_DATE, ADD_DESC, \
    REMOVE_DATE, REMOVE_SEL
from py_func.stock import \
    stock_start, add_dir, add_market, \
    add_stock_code, add_stock_price, \
    add_stock_lot, add_stock_broker, add_done, \
    SHOW_SMY, ADD_DIR, ADD_MKT, \
    ADD_CODE, ADD_PRICE, ADD_LOT, \
    ADD_BRK, ADD_DONE

# get environment vars
parser = argparse.ArgumentParser()
parser.add_argument('--botkey', help='Key from bot father')
args = parser.parse_args()

# Bot Credential
updater = Updater(args.botkey, use_context=True)

if __name__ == '__main__':
    # Define /bbi handler workflow
    bbi_handler = ConversationHandler(
        entry_points=[CommandHandler('bbi', bbi_start)],
        states={
            ROUTE: [
                MessageHandler(
                    Filters.regex('^\w?[0-9]+\w?$'), bbi_callback_handler,
                ),
            ],
            DEST: [CallbackQueryHandler(bbi_callback_handler)],
            SEC_ROUTE: [CallbackQueryHandler(bbi_callback_handler)],
        },
        fallbacks=[CommandHandler('end', conv_end)],
    )

    # Define /counter handler workflow
    counter_handler = ConversationHandler(
        entry_points=[CommandHandler('counter', date_counter)],
        states={
            SHOW_DATE: [
                MessageHandler(Filters.regex('(?i)add'), add_dates_handler),
                MessageHandler(
                    Filters.regex('(?i)remove'),
                    remove_dates_handler,
                ),
            ],
            ADD_DATE: [
                MessageHandler(
                    Filters.regex('^\d{4}\-\d{1,2}\-\d{1,2}$'),
                    add_dates_handler,
                ),
            ],
            ADD_DESC: [
                MessageHandler(
                    Filters.regex('\w+'), add_dates_handler,
                ),
            ],
            REMOVE_DATE: [CallbackQueryHandler(remove_dates_handler)],
            REMOVE_SEL: [CallbackQueryHandler(remove_dates_handler)],
        },
        fallbacks=[CommandHandler('end', conv_end)],
    )

    # Define /stock handler workflow
    stock_handler = ConversationHandler(
        entry_points=[CommandHandler('stock', stock_start)],
        states={
            SHOW_SMY: [CommandHandler('trade', add_dir)],
            ADD_DIR: [CallbackQueryHandler(add_market)],
            ADD_MKT: [CallbackQueryHandler(add_stock_code)],
            ADD_CODE: [
                MessageHandler(Filters.regex('\w+'), add_stock_price),
            ],
            ADD_PRICE: [
                MessageHandler(
                    Filters.regex('\d+(\.\d{1,2})?'),
                    add_stock_lot,
                ),
            ],
            ADD_LOT: [
                MessageHandler(Filters.regex('^[1-9]\d*$'), add_stock_broker),
            ],
            ADD_BRK: [CallbackQueryHandler(add_done)],
            ADD_DONE: [
                CommandHandler('trade', add_dir),
                CommandHandler('stock', stock_start),
            ],
        },
        fallbacks=[CommandHandler('end', conv_end)],
    )

    dp = updater.dispatcher
    # /hi
    dp.add_handler(CommandHandler('hi', greet))
    # /counter
    dp.add_handler(counter_handler)
    # /bbi
    dp.add_handler(bbi_handler)
    # /stock
    dp.add_handler(stock_handler)
    # error handler
    dp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
