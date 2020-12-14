from datetime import datetime, time
from dateutil.relativedelta import relativedelta
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    CallbackQueryHandler, callbackcontext, ConversationHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# initialize response list
from py_func.bbi_info import get_bbi_info
from py_func.layout_config import build_menu

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

# Bot Credential
updater = Updater('1460342157:AAH26oIP5bwvL6SMgx3lE4BsiQLnAiidGQ8', use_context=True)

# Global vars:
ROUTE, DEST, SEC_ROUTE = range(3)
STATE = ROUTE
bbi_res_lst = dict()


def greet(update, context):
    """/greeting"""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Hi BB, this is our bot!! Press command to start\n\n '
             '/counter Trigger time machine\n\n '
             '/bbi Check Bus Interchange info\n\n'
    )


# def counter(update, context):
#     """/start"""
#     context.bot.send_message(chat_id=update.effective_chat.id, text='Hi BB, this is our AI reminder')
#     # updater.job_queue.run_repeating(date_counter, context=update.effective_chat.id, interval=86400,  first=0.1)


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Unknown Command')


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{update.message.text}")


# Periodic reminder
def date_counter(update, context):
    today = datetime.now()
    anniversary = datetime(2019, 9, 6)
    meet_date = datetime(2019, 5, 23)
    first_date = datetime(2019, 6, 9)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'❤❤❤❤❤ Daily Summary {datetime.now().strftime("%Y-%m-%d")} ❤❤❤❤❤'
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Happy {(today - anniversary).days} Days!\n'
             f'{relativedelta(today, meet_date).years * 12 + relativedelta(today, meet_date).months} '
             f'months since first chat \n'
             f'{relativedelta(today, first_date).years * 12 + relativedelta(today, first_date).months} '
             f'months since first date \n'
             f'{relativedelta(today, anniversary).years * 12 + relativedelta(today, anniversary).months} '
             f'months since anniversary '
    )


# BBI function collection
def bbi_start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Enter the 1st Route'
    )
    return ROUTE


def bbi_callback_handler(update, context):
    """handle BBI callback"""

    if update.callback_query is None:
        route = update.message.text
        bbi_dict = get_bbi_info(route)
        btn_directions = list(bbi_dict.keys())

        lst_button = list()
        for i in btn_directions:
            lst_button.append(InlineKeyboardButton(i, callback_data=str(i)))

        reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=1))

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'You have chosen Route {route}'
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'/bbi-sel Select Direction',
            reply_markup=reply_markup
        )
        bbi_res_lst['route'] = route
        bbi_res_lst['detail'] = bbi_dict

        return DEST

    elif update.callback_query.message.text.split(' ')[0] == '/bbi-sel':
        destination = update.callback_query.data
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'/bbi-dest {destination}'
        )

        bbi_dict = bbi_res_lst['detail'][destination]
        bbi_res_lst['detail'] = bbi_dict

        lst_chg = [i['sec_routeno'] for i in bbi_dict]

        lst_button = list()
        for i in lst_chg:
            lst_button.append(InlineKeyboardButton(i, callback_data=str(i)))

        reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=5))
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'You Can Change the following routes'
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'/bbi-xchg List of 2nd routes',
            reply_markup=reply_markup
        )

        return SEC_ROUTE

    elif update.callback_query.message.text.split(' ')[0] == '/bbi-xchg':
        route_chosen = update.callback_query.data
        bbi_dict = bbi_res_lst['detail']

        change_dir = [i['sec_dest'] for i in bbi_dict if i['sec_routeno'] == route_chosen][0]
        change_dest = [i['xchange'] for i in bbi_dict if i['sec_routeno'] == route_chosen][0]
        fare_detail = [i['discount_max'] for i in bbi_dict if i['sec_routeno'] == route_chosen][0]

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'++++++++++++++++++++++++++++++\n'
                                      f'Change {route_chosen} to {change_dir}\n\n'
                                      f'Change stop : {change_dest}\n\n'
                                      f'Fare discount : {fare_detail}\n\n'
                                      'press /end to end this inquiry',
                                 )


def conv_end(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'See you! Input /hi to call me again :D'
    )
    return ConversationHandler.END


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
