import ast
from datetime import datetime
from decimal import Decimal
import json
import numpy as np
import pandas as pd
import requests
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from . import build_menu
from .dynamodb_exchange import scan_db, batch_process_items, insert_item, fetch_item_by_key

# Global vars:
SHOW_SMY, ADD_DIR, ADD_MKT, ADD_CODE, ADD_PRICE, ADD_LOT, ADD_BRK, ADD_DONE = range(8)
new_txn_record = dict()
lst_holding = list()


def stock_start(update, context):

    return_text = ""
    lst_code = list()
    lst_holding.clear()
    total_pnl = 0
    total_pnl_hkd = 0
    total_pnl_usd = 0

    lst_holding.append(fetch_item_by_key(
        db_table='stock_holding',
        item={'user': update.message.from_user.username}
    )[0])
    for holding in lst_holding[0]:

        if holding['market'] != 'US':
            code = f"{holding['code'].zfill(4)}.{holding['market']}"
        else:
            code = holding['code']
        lst_code.append(code)

    quote_dict = quote_price(lst_code)

    for idx, holding in enumerate(lst_holding[0]):

        try:

            unrealized_gain = holding['available_sell'] * (
                        Decimal(quote_dict[idx]['regularMarketPrice']) - holding['avg_price'])

            if holding['market'] == 'HK':
                total_pnl += unrealized_gain + holding['realized_gain']
                total_pnl_hkd = total_pnl
            elif holding['market'] == 'US':
                total_pnl += (unrealized_gain + holding['realized_gain']) * Decimal(7.8)
                total_pnl_usd += unrealized_gain + holding['realized_gain']

            return_text += f"{holding['market']}\t{holding['code']}\n" \
                           f"{quote_dict[idx]['longName']}\n" \
                           f"Current price: {quote_dict[idx]['regularMarketPrice']}\n\n" \
                           f"Average buy price: {round(holding['avg_price'], 3)}\n" \
                           f"Available to sell: {holding['available_sell']}\n\n" \
                           f"Realized gain: {round(holding['realized_gain'], 0)}\n" \
                           f"Unrealized P/L: {round(unrealized_gain,0)}\n" \
                           f"Total P/L: {round(unrealized_gain + holding['realized_gain'],0)}\n" \
                           f"({quote_dict[idx]['quoteSourceName']})\n" \
                           f"------------------------------------------\n"
        except:
            return_text += f"{holding['market']}\t{holding['code']}\n" \
                           f"Average buy price: {round(holding['avg_price'], 3)}\n" \
                           f"Available to sell: {holding['available_sell']}\n\n" \
                           f"Realized gain: {round(holding['realized_gain'], 0)}\n" \
                           f"(Data is not available from Yahoo API)\n" \
                           f"------------------------------------------\n"

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Here's your current holding summary !\n\n"
             f"Total P/L in HKD : {round(total_pnl,0)}\n"
             f"By Market:\n"
             f"HKD : {round(total_pnl_hkd,0)}\n"
             f"USD: {round(total_pnl_usd,0)}\n\n"
             f"Holdings right now,,\n\n"
             f"{return_text}\n\n"
             'reply /trade to add new trade records\n',
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
        text='Done! click /end >> /stock to check your latest statement \n'
             'or click /trade to add another transaction',
    )

    insert_item(db_table='stock_txn', item=new_txn_record)

    return ADD_DONE


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
        'x-rapidapi-key': "5c2f24892fmsh58278fdf1cebf0fp1bb586jsndda6a2eceff8",
        'x-rapidapi-host': "yahoo-finance-low-latency.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    return json.loads(response.text)['quoteResponse']['result']


def update_summary():
    """
    Update txn records and re-generate holding summary
    :return:
    """
    result = scan_db(db_table='stock_txn', key='user', cond='erikws')
    txn = pd.DataFrame(result)

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


update_summary()
