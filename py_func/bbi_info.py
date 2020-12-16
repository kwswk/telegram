import requests
import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from . import build_menu

# Global vars:
ROUTE, DEST, SEC_ROUTE = range(3)
bbi_res_lst = dict()


def get_bbi_info(route: object) -> dict:
    direction = ['F', 'B']
    bbi_info = list()
    for i in direction:
        conn = requests.get(f'http://www.kmb.hk/ajax/BBI/get_BBI2-en.php?routeno={route}&bound={i}')
        bbi_raw = json.loads(conn.text)
        bbi_info.append(bbi_raw)

    bbi_dict = {i['bus_arr'][0]['dest']: i['Records'] for i in bbi_info}

    return bbi_dict


def bbi_start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Enter the 1st Route',
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
            text=f'You have chosen Route {route}',
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'/bbi-sel Select Direction',
            reply_markup=reply_markup,
        )
        bbi_res_lst['route'] = route
        bbi_res_lst['detail'] = bbi_dict

        return DEST

    elif update.callback_query.message.text.split(' ')[0] == '/bbi-sel':
        destination = update.callback_query.data
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'/bbi-dest {destination}',
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
            text=f'You Can Change the following routes',
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'/bbi-xchg List of 2nd routes',
            reply_markup=reply_markup,
        )

        return SEC_ROUTE

    elif update.callback_query.message.text.split(' ')[0] == '/bbi-xchg':
        route_chosen = update.callback_query.data
        bbi_dict = bbi_res_lst['detail']

        change_dir = [i['sec_dest'] for i in bbi_dict if i['sec_routeno'] == route_chosen][0]
        change_dest = [i['xchange'] for i in bbi_dict if i['sec_routeno'] == route_chosen][0]
        fare_detail = [i['discount_max'] for i in bbi_dict if i['sec_routeno'] == route_chosen][0]

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'++++++++++++++++++++++++++++++\n'
                 f'Change {route_chosen} to {change_dir}\n\n'
                 f'Change stop : {change_dest}\n\n'
                 f'Fare discount : {fare_detail}\n\n'
                 'press /end to end this inquiry',
         )