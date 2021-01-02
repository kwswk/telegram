from datetime import datetime
from decimal import Decimal
import json
import numpy as np
import pandas as pd
import requests

from .dynamodb_exchange import scan_db, batch_insert_items


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

    print(response.text)
    return response.text


def update_summary():
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


update_summary()
