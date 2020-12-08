from datetime import datetime
from dateutil.relativedelta import relativedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, callbackcontext
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# initialize response list
from py_func.bbi_info import get_bbi_info
from py_func.layout_config import build_menu

updater = Updater('1460342157:AAH26oIP5bwvL6SMgx3lE4BsiQLnAiidGQ8', use_context=True)
timer = updater.job_queue

bbi_res_lst = dict()


def start(update, context):
    """/start"""
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hi BB, this is our AI reminder')
    updater.job_queue.run_repeating(date_counter, interval=86400, context=update.effective_chat.id)


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Unknown Command')


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{update.message.text}")


# Periodic reminder
def date_counter(context: callbackcontext):
    today = datetime.now()
    anniversary = datetime(2019, 9, 6)
    meet_date = datetime(2019, 5, 23)
    first_date = datetime(2019, 6, 9)

    context.bot.send_message(chat_id=context.job.context, text=f'❤❤❤❤❤ Daily Summary {datetime.now()} ❤❤❤❤❤')
    context.bot.send_message(
        chat_id=context.job.context,
        text=f'Happy {(today-anniversary).days} Days!'
    )
    context.bot.send_message(
        chat_id=context.job.context,
        text=f'{relativedelta(today,meet_date).years * 12 + relativedelta(today,meet_date).months} '
             f'months since first chat '
    )
    context.bot.send_message(
        chat_id=context.job.context,
        text=f'{relativedelta(today,first_date).years * 12 + relativedelta(today,first_date).months} '
             f'months since first date '
    )
    context.bot.send_message(
        chat_id=context.job.context,
        text=f'{relativedelta(today, anniversary).years * 12 + relativedelta(today, anniversary).months} '
             f'months since anniversary '
    )


# BBI function
def bbi_command_handler(update, context):
    route = context.args[0]
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


def bbi_callback_handler(update, context):
    """handle BBI callback"""

    if update.callback_query.message.text.split(' ')[0] == '/bbi-sel':
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

    elif update.callback_query.message.text.split(' ')[0] == '/bbi-xchg':
        route_chosen = update.callback_query.data
        bbi_dict = bbi_res_lst['detail']

        change_dir = [i['sec_dest'] for i in bbi_dict if i['sec_routeno'] == route_chosen][0]
        change_dest = [i['xchange'] for i in bbi_dict if i['sec_routeno'] == route_chosen][0]
        fare_detail = [i['discount_max'] for i in bbi_dict if i['sec_routeno'] == route_chosen][0]

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'++++++++++++++++++++++++++++++',
                                 )
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Change {route_chosen} to {change_dir}',
                                 )
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Change stop : {change_dest}',
                                 )
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Fare discount : {fare_detail}',
                                 )


if __name__ == '__main__':

    """add functions to dispatcher"""
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))

    """custom functions"""
    dp.add_handler(CommandHandler('bbi', bbi_command_handler))
    dp.add_handler(CallbackQueryHandler(bbi_callback_handler))

    # dp.add_handler(CommandHandler('dating', date_counter, pass_job_queue=True))

    """Unknown handler"""
    dp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()


