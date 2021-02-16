import json
import os
import requests

from telegram import ReplyKeyboardMarkup

# Global vars:
FX_FROM, FX_TO, FX_RATE = range(3)


def get_rate(curr: str):

    url = f'https://rest.coinapi.io/v1/exchangerate/{curr}?invert=false'

    headers = {
        'X-CoinAPI-Key': os.environ['coinapikey']
    }
    return json.loads(requests.get(url, headers=headers).text)


def currency_button() -> ReplyKeyboardMarkup:
    lst_button = ['HKD', 'USD', 'EUR', 'GBP', 'JPY', 'BTC', 'ETH']
    return ReplyKeyboardMarkup(
        [[button] for button in lst_button],
        one_time_keyboard=True,
        resize_keyboard=True,
    )


def ask_from_curr(update, context) -> int:

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='What is your base currency? (Choose below or enter manually)',
        reply_markup=currency_button(),
    )

    return FX_FROM


def ask_to_curr(update, context) -> int:

    global rate
    rate = get_rate(update.message.text)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='And target currency? (Choose below or enter manually)',
        reply_markup=currency_button(),
    )

    return FX_TO


def return_rate(update, context) -> int:

    base_curr = rate['asset_id_base']
    target_rate = [
        cur for cur in rate['rates']
        if cur['asset_id_quote'] == update.message.text
    ].pop()

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'💰💰 From {base_curr} to {update.message.text}\n'
             + f"Latest Rate: {target_rate['rate']}\n"
             + f"Update time: {target_rate['time']}\n\n"
             + f"Continue to check other rate by clicking currencies\n\n"
             + f"or click /fx to change base currency\n\n"
             + f"or /end to quit",
        reply_markup=currency_button(),
    )

    return FX_RATE



