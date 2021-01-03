from datetime import datetime
from decimal import Decimal
import json
import numpy as np
import pandas as pd
import requests
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from . import build_menu
from .dynamodb_exchange import scan_db, batch_insert_items, insert_item

# Global vars:
SHOW_SMY, ADD_DIR, ADD_MKT, ADD_CODE, ADD_PRICE, ADD_LOT, ADD_BRK, ADD_DONE = range(8)
new_txn_record = dict()


def stock_start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Here's your stock summary\n\n"
             'reply "trade" to add new trade records\n',
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
    new_txn_record['load_date'] = datetime.now().strftime('%Y-%m-%d')

    return ADD_DIR


def add_market(update, context):

    new_txn_record['direction'] = update.callback_query.data
    lst_button = list()
    lst_mkt = ['HK', 'US', 'CRYPTO']

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

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Okay! Tell me the stock code',
    )

    return ADD_CODE


def add_stock_price(update, context):

    new_txn_record['code'] = update.message.text.upper()

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='At what price?',
    )

    return ADD_PRICE


def add_stock_lot(update, context):

    if new_txn_record['direction'] == 'BUY':
        new_txn_record['buy_price'] = Decimal(update.message.text)
    else:
        new_txn_record['sold_price'] = Decimal(update.message.text)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='And quantity?',
    )

    return ADD_LOT


def add_stock_broker(update, context):

    if new_txn_record['direction'] == 'BUY':
        new_txn_record['buy_lot'] = Decimal(update.message.text)
    else:
        new_txn_record['sold_lot'] = Decimal(update.message.text)

    lst_button = list()
    lst_broker = ['FUTU', 'BOC', 'CITI', 'TD', 'IB', 'WIREX']

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
        text='Done! click /end >> /stock to check your latest statement',
    )

    insert_item(db_table='stock_txn', item=new_txn_record)

    return ADD_DONE


def quote_price(market, code):
    """
    calling Yahoo API (100 requests per day)
    :param market: US or HK
    :param code: Stock Code
    :return: Dict of price
    """

    if market != 'US':
        code = f'{code.zfill(4)}.{market}'

    url = "https://yahoo-finance-low-latency.p.rapidapi.com/v6/finance/quote"

    querystring = {"symbols": code}

    headers = {
        'x-rapidapi-key': "5c2f24892fmsh58278fdf1cebf0fp1bb586jsndda6a2eceff8",
        'x-rapidapi-host': "yahoo-finance-low-latency.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    return response.text


def update_summary():
    """
    Update txn records and re-generate holding summary
    :return:
    """
    result = scan_db(db_table='stock_txn', key='user', cond='erikws')
    txn = pd.DataFrame(result)

    txn.columns = txn.columns.str.strip()
    txn = txn.sort_values(by=['user', 'code', 'date', 'direction']).fillna(0)

    num_vars = ['buy_lot', 'sold_lot', 'buy_price', 'sold_price']
    for col in num_vars:
        txn[col] = txn[col].astype(float)
    txn['date'] = pd.to_datetime(txn.date)
    txn['code'] = txn['code'].astype(str)

    txn['cum_buy'] = txn.groupby(['user', 'code'])['buy_lot'].cumsum()
    txn['cum_book_value'] = txn.assign(col=txn.buy_lot * txn.buy_price).groupby(['user', 'code']).col.cumsum()
    txn['cum_sell'] = txn.groupby(['user', 'code'])['sold_lot'].cumsum()
    txn['available_sell'] = txn['cum_buy'] - txn['cum_sell']
    txn['avg_price'] = txn.cum_book_value / txn.cum_buy

    # Get Status
    txn.loc[txn.available_sell == 0, 'settle_date'] = txn.date
    txn.settle_date = txn.settle_date.fillna(datetime(1900, 1, 1))
    txn['settle_date'] = txn.groupby(['user', 'code'])['settle_date'].transform('max')
    txn['status'] = np.where(txn.date > txn.settle_date, 'OPEN', 'CLOSE')

    # Current holding summary
    stock_holding = txn.loc[
        (txn.groupby(['user', 'code'])['date'].transform(max) == txn.date) & (txn.status == 'OPEN'),
        ['user', 'code', 'market', 'cum_book_value', 'available_sell', 'avg_price']
    ]

    export_data = json.loads(stock_holding.to_json(orient="records"), parse_float=Decimal)

    batch_insert_items('stock_holding', export_data, ['user', 'code'])
