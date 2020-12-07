from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import replykeyboardmarkup, InlineKeyboardMarkup, InlineKeyboardButton
from bbi_info import get_bbi_info
from typing import List, Dict, Any

# initialize response list
bbi_res_lst = dict()


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """fix layout of long list of inline buttons"""
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def start(update, context):
    """/start"""
    context.bot.send_message(chat_id=update.effective_chat.id, text="hey bb, try my breast!")


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{update.message.text}")


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def bbi_res_hist(scope, response):
    bbi_res_lst[scope] = response


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
    bbi_res_hist('route', route)
    bbi_res_hist('detail', bbi_dict)


def bbi_callback_handler(update, context):
    """handle BBI callback"""

    if update.callback_query.message.text.split(' ')[0] == '/bbi-sel':
        destination = update.callback_query.data
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'/bbi-dest {destination}'
        )

        bbi_dict = bbi_res_lst['detail'][destination]
        bbi_res_hist('detail', bbi_dict)

        lst_chg = [i['sec_routeno'] for i in bbi_dict]

        lst_button = list()
        for i in lst_chg:
            lst_button.append(InlineKeyboardButton(i, callback_data=str(i)))

        reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=3))
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
    updater = Updater('1460342157:AAH26oIP5bwvL6SMgx3lE4BsiQLnAiidGQ8', use_context=True)

    """add functions to dispatcher"""
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))

    """custom functions"""
    dp.add_handler(CommandHandler('bbi', bbi_command_handler))
    dp.add_handler(CallbackQueryHandler(bbi_callback_handler))

    """Unknown handler"""
    dp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
