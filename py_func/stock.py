import ast
from datetime import datetime
from decimal import Decimal
import json
import os
import requests
import uuid

import flag
import numpy as np
import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from . import build_menu
from .dynamodb_exchange import scan_db, batch_process_items, insert_item, fetch_item_by_key

# Global vars:
SHOW_SMY, ADD_DIR, ADD_MKT, ADD_CODE, ADD_PRICE, ADD_LOT, ADD_BRK, ADD_DONE, \
REMOVE_CODE, REMOVE_TXN, REMOVE_DONE = range(11)
new_txn_record = dict()
lst_holding = list()
list_remove = list()


def stock_start(update, mode):
    lst_code = list()
    lst_holding.clear()
    list_remove.clear()

    return_text = ""
    day_pnl = 0
    day_pnl_hkd = 0
    day_pnl_usd = 0
    total_value = 0
    total_pnl = 0
    total_pnl_hkd = 0
    total_pnl_usd = 0

    if mode == 1:
        user = update.message.from_user.username
    else:
        user = update.callback_query.from_user.username

    lst_holding.append(
        fetch_item_by_key(
            db_table='stock_holding',
            item={'user': user}
        )[0]
    )

    if len(lst_holding[0]) > 0:

        for holding in lst_holding[0]:

            if holding['market'] != 'US':
                code = f"{holding['code'].zfill(4)}.{holding['market']}"
            else:
                code = holding['code']
            lst_code.append(code)

            list_remove.append({'user': user, 'code': holding['code']})

        quote_dict = quote_price(lst_code)

        for idx, holding in enumerate(lst_holding[0]):

            try:
                market_value = Decimal(quote_dict[idx]['regularMarketPrice']) * holding['available_sell']

                unrealized_gain = holding['available_sell'] * (
                        Decimal(quote_dict[idx]['regularMarketPrice']) - holding['avg_price']
                )
                delta_unit_gain = \
                    (quote_dict[idx]['regularMarketPrice'] - quote_dict[idx]['regularMarketPreviousClose']) \
                    * float(holding['available_sell'])

                if holding['market'] == 'HK':
                    total_value += market_value
                    total_pnl += unrealized_gain + holding['realized_gain']
                    total_pnl_hkd = total_pnl
                    day_pnl += delta_unit_gain
                    day_pnl_hkd = day_pnl
                elif holding['market'] == 'US':
                    total_value += market_value * Decimal(7.8)
                    total_pnl += (unrealized_gain + holding['realized_gain']) * Decimal(7.8)
                    total_pnl_usd += unrealized_gain + holding['realized_gain']
                    day_pnl += delta_unit_gain * 7.8
                    day_pnl_usd = day_pnl

                return_text += f"{flag.flag(holding['market'])}\t{holding['code']}\n" \
                               f"{quote_dict[idx]['longName']}\n" \
                               f"Current price: {quote_dict[idx]['regularMarketPrice']:,}\n\n" \
                               f"Average buy price: {round(holding['avg_price'], 3):,}\n" \
                               f"Available to sell: {holding['available_sell']:,}\n" \
                               f"Market Value: {round(market_value, 0):,}\n\n" \
                               f"Day P/L: $ {delta_unit_gain:,.1f}\n" \
                               f"Realized P/L: {round(holding['realized_gain'], 0):,}\n" \
                               f"Unrealized P/L: {round(unrealized_gain, 0):,}\n" \
                               f"Total P/L: {round(unrealized_gain + holding['realized_gain'], 0):,}\n" \
                               f"({quote_dict[idx]['quoteSourceName']})\n" \
                               f"------------------------------------------\n"
            except:
                return_text += f"{flag.flag(holding['market'])}\t{holding['code']}\n" \
                               f"Average buy price: {round(holding['avg_price'], 3):,}\n" \
                               f"Available to sell: {holding['available_sell']:,}\n\n" \
                               f"Realized P/L: {round(holding['realized_gain'], 0):,}\n" \
                               f"(Data is not available from Yahoo API)\n" \
                               f"------------------------------------------\n"

    return f"Here's your current holding summary !!\n\n" \
           + f"📈Book value: $ {round(total_value, 0):,}\n" \
           + f"Total P/L (HKD) :  $ {round(total_pnl, 0):,} / $ {round(day_pnl, 0):,} (Day) \n\n" \
           + f"🏳️‍🌈By Market:\n" \
           + f"{flag.flag('HK')} : $ {round(total_pnl_hkd, 0):,} / $ {round(day_pnl_hkd, 0):,} (Day) \n" \
           + f"{flag.flag('US')} : $ {round(total_pnl_usd, 0):,} / $ {round(day_pnl_usd, 0):,} (Day) \n\n" \
           + f"😻😻😻 Holdings right now 😻😻😻\n\n" \
           + f"{return_text}\n\n" \
           + 'Click /trade to add new trade records\n\n' \
           + 'Click /remove to remove wrong records\n\n' \
           + 'or click /end to end this session\n\n' \
           + f'Update time: {datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}'


def stock_summary_init(update, context):
    reply_markup = InlineKeyboardMarkup(
        build_menu(
            [InlineKeyboardButton('Update summary', callback_data='Update summary')],
            n_cols=1,
        ),
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=stock_start(update, 1),
        reply_markup=reply_markup,
    )
    return SHOW_SMY


def stock_summary_update(update, context):
    reply_markup = InlineKeyboardMarkup(
        build_menu(
            [InlineKeyboardButton('Update summary', callback_data='Update summary')],
            n_cols=1,
        ),
    )

    context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id,
        text=stock_start(update, 2),
        reply_markup=reply_markup,
    )
    return SHOW_SMY


def add_dir(update, context):
    new_txn_record.clear()
    lst_button = list()
    lst_dir = ['BUY', 'SELL']

    for direction in lst_dir:
        lst_button.append(
            InlineKeyboardButton(direction, callback_data=str(direction)),
        )

    reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=2))

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Tell me the direction',
        reply_markup=reply_markup,
    )

    new_txn_record['txn_id'] = uuid.uuid4().hex
    new_txn_record['user'] = update.message.from_user.username
    new_txn_record['date'] = datetime.now().strftime('%Y-%m-%d')

    return ADD_DIR


def add_market(update, context):
    new_txn_record['direction'] = update.callback_query.data
    lst_button = list()
    lst_mkt = ['HK', 'US']

    for market in lst_mkt:
        lst_button.append(
            InlineKeyboardButton(market, callback_data=str(market)),
        )

    reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=3))

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Which market is it?',
        reply_markup=reply_markup,
    )

    return ADD_MKT


def add_stock_code(update, context):
    new_txn_record['market'] = update.callback_query.data

    if new_txn_record['direction'] == 'BUY':
        reply_markup = None
    else:
        lst_button = list()

        for i in lst_holding[0]:
            if i['market'] == update.callback_query.data:
                lst_button.append(
                    InlineKeyboardButton(
                        i['code'],
                        callback_data=str(i['code']),
                    ),
                )

        reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=4))

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Okay! Tell me the stock code',
        reply_markup=reply_markup,
    )

    return ADD_CODE


def add_stock_price(update, context):

    if new_txn_record['direction'] == 'BUY':
        new_txn_record['code'] = update.message.text.upper()
    else:
        new_txn_record['code'] = update.callback_query.data

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='At what price?',
    )

    return ADD_PRICE


def add_stock_lot(update, context):
    if new_txn_record['direction'] == 'BUY':
        new_txn_record['buy_price'] = Decimal(update.message.text)
        new_txn_record['sold_price'] = None
        reply_markup = None
    else:
        new_txn_record['buy_price'] = None
        new_txn_record['sold_price'] = Decimal(update.message.text)
        avail_sell = [
            float(stock['available_sell'])
            for stock in lst_holding[0]
            if stock['code'] == new_txn_record['code']
        ]
        reply_markup = InlineKeyboardMarkup(
            build_menu(
                [InlineKeyboardButton(f'Clear (Total: {avail_sell})', callback_data=str(avail_sell[0]))],
                n_cols=1,
            ),
        )

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='And quantity? Enter number or click Clear button',
        reply_markup=reply_markup
    )

    return ADD_LOT


def add_stock_broker(update, context):
    if new_txn_record['direction'] == 'BUY':
        new_txn_record['buy_lot'] = Decimal(update.message.text)
        new_txn_record['sold_lot'] = None
    else:
        new_txn_record['buy_lot'] = None
        try:
            new_txn_record['sold_lot'] = Decimal(update.message.text)
        except AttributeError:
            new_txn_record['sold_lot'] = Decimal(update.callback_query.data)

    lst_button = list()
    lst_broker = ['FUTU', 'BOC', 'CITI', 'TD', 'BINANCE', 'WIREX']

    for broker in lst_broker:
        lst_button.append(
            InlineKeyboardButton(broker, callback_data=str(broker)),
        )

    reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=3))

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Final Question, which broker?',
        reply_markup=reply_markup,
    )

    return ADD_BRK


def add_done(update, context):
    new_txn_record['broker'] = update.callback_query.data

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Done! \n'
             'Click  /stock to checkout your latest statement \n\n'
             'Click /trade to add another transaction \n\n'
             'Click /end to end this session',
    )

    insert_item(db_table='stock_txn', item=new_txn_record)

    try:
        batch_process_items('stock_holding', items=list_remove, keys=['user', 'code'], method='delete')
    except:
        pass

    update_summary(update.callback_query.from_user.username)

    return ADD_DONE


def remove_code_select(update, context):
    lst_button = list()

    for i in lst_holding[0]:
        lst_button.append(
            InlineKeyboardButton(
                f"{i['market']} - {i['code']}",
                callback_data=str(i['code']),
            )
        )

    reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=4))

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Which stock got input error?',
        reply_markup=reply_markup,
    )
    return REMOVE_CODE


def remove_txn_select(update, context):
    result = scan_db(
        db_table='stock_txn',
        key='user',
        cond=update.callback_query.from_user.username,
        key2='code',
        cond2=update.callback_query.data,
    )

    lst_button = list()

    for i in result:
        if i['buy_lot'] is not None:
            reply = f"[{i['broker']}] {i['date']} BUY {str(i['buy_lot'])} @ {str(i['buy_price'])}"
        else:
            reply = f"[{i['broker']}] {i['date']} SOLD {str(i['sold_lot'])} @ {str(i['sold_price'])}"

        lst_button.append(
            InlineKeyboardButton(reply, callback_data=str(i['txn_id']))
        )

    reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=1))

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Which stock got input error?',
        reply_markup=reply_markup,
    )
    return REMOVE_TXN


def remove_txn_done(update, context):
    rec_remove = [dict(
        txn_id=update.callback_query.data,
        user=update.callback_query.from_user.username,
    )]
    batch_process_items('stock_txn', items=rec_remove, keys=['txn_id', 'user'], method='delete')

    try:
        batch_process_items('stock_holding', items=list_remove, keys=['user', 'code'], method='delete')
    except:
        pass

    update_summary(update.callback_query.from_user.username)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Remove done!\n\n'
             'click /stock to review your updated summary\n\n'
             'click /remove to remove more\n\n'
             'or click /end to kill this session',
    )

    return REMOVE_DONE


def quote_price(code_list: list) -> dict:
    """
    calling Yahoo API (100 requests per day)
    :param code_list: List of Stock Code
    :return: Dict of price
    """

    quote_str = ','.join(code_list)

    url = "https://yahoo-finance-low-latency.p.rapidapi.com/v6/finance/quote"

    querystring = {"symbols": quote_str}

    headers = {
        'x-rapidapi-key': os.environ['rapidapikey'],
        'x-rapidapi-host': os.environ['rapidapihost'],
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    return json.loads(response.text)['quoteResponse']['result']


def update_summary(user_name):
    """
    Update txn records and re-generate holding summary
    :return:
    """
    result = scan_db(db_table='stock_txn', key='user', cond=user_name)
    txn = pd.DataFrame(result)

    txn = txn.sort_values(by=['user', 'code', 'date', 'direction']).fillna(0)

    num_vars = ['buy_lot', 'sold_lot', 'buy_price', 'sold_price']
    for col in num_vars:
        txn[col] = txn[col].astype(float)
    txn['date'] = pd.to_datetime(txn.date)
    txn['code'] = txn['code'].astype(str)

    txn['cum_buy'] = txn.groupby(['user', 'code'])['buy_lot'].cumsum()
    txn['cum_sell'] = txn.groupby(['user', 'code'])['sold_lot'].cumsum()
    txn['available_sell'] = txn['cum_buy'] - txn['cum_sell']

    # Get Status
    txn.loc[txn.available_sell == 0, 'settle_date'] = txn.date
    txn.settle_date = txn.settle_date.fillna(datetime(1900, 1, 1))
    txn['settle_date'] = txn.groupby(['user', 'code'])['settle_date'].transform('max')
    txn['status'] = np.where(txn.date > txn.settle_date, 'OPEN', 'CLOSE')

    # Get avg price
    txn['cum_buy'] = txn.groupby(['user', 'code', 'status'])['buy_lot'].cumsum()
    txn['cum_book_value'] = txn.assign(col=txn.buy_lot * txn.buy_price).groupby(['user', 'code', 'status']).col.cumsum()
    txn['avg_price'] = txn.cum_book_value / txn.cum_buy
    txn['realized_gain'] = txn.assign(col=txn.sold_lot * (txn.sold_price - txn.avg_price)).groupby(
        ['user', 'code', 'status']).col.cumsum()

    # Current holding summary
    stock_holding = txn.loc[
        (txn.groupby(['user', 'code'])['date'].transform(max) == txn.date) & (txn.status == 'OPEN'),
        ['user', 'code', 'market', 'available_sell', 'avg_price', 'realized_gain']
    ]

    export_data = json.loads(
        stock_holding.to_json(orient="records"), parse_float=Decimal
    )

    batch_process_items('stock_holding', export_data, ['user', 'code'])
