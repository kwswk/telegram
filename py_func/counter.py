import ast
from datetime import datetime
from dateutil.relativedelta import relativedelta

import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from . import build_menu
from .dynamodb_exchange import insert_item, fetch_item_by_key, delete_item

# Global vars:
SHOW_DATE, ADD_DATE, ADD_DESC, ADD_DONE, REMOVE_DATE, REMOVE_SEL, REMOVE_DONE = range(7)
item_date = dict()
dates = list()


def add_dates_handler(update, context):
    """
    handle ADD action after calling counter
    :param update: from bot API
    :param context: from bot API
    :return:
            ADD_DATE : step 1
            ADD_DESC : step 2
            ADD_DONE : step 3
    """
    if re.match('(?i)add', update.message.text):
        user = 'erikws' if update.message.from_user.username == 'sleepyforever' else update.message.from_user.username
        item_date['user'] = user
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Tell me the date in YYYY-MM-DD format'
        )
        return ADD_DATE

    elif re.match('^\d{4}\-\d{1,2}\-\d{1,2}$', update.message.text):
        item_date['date'] = update.message.text
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='What is it about'
        )
        return ADD_DESC

    else:
        item_date['desc'] = update.message.text
        insert_item(db_table='important_dates', item=item_date)

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Insert Done!\n'
                 'Click /end then /counter to check new timer'
        )

        return ADD_DONE


def remove_dates_handler(update, context):
    """
    handle REMOVE action after calling counter
    :param update: from bot API
    :param context: from bot API
    :return:
            REMOVE_DATE : step 1
            REMOVE_SEL : step 2
            REMOVE_DONE : step 3
    """
    if update.message is not None:

        if re.match('(?i)remove', update.message.text):

            lst_button = list()

            for i in dates[0]:
                lst_button.append(
                    InlineKeyboardButton(
                        f"{i['desc']}, {i['date']}",
                        callback_data=str(i),
                    )
                )

            reply_markup = InlineKeyboardMarkup(build_menu(lst_button, n_cols=1))

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Tell me the date you gonna remove',
                reply_markup=reply_markup,
            )
            return REMOVE_DATE

    elif update.callback_query.message.text == 'Tell me the date you gonna remove':

        del_feedback = ast.literal_eval(update.callback_query.data)
        delete_item(
            'important_dates',
            item={k: del_feedback[k] for k in ['user','date'] if del_feedback}
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Remove Done!\n'
                 'Click /end then /counter to check new timer'
        )
        return REMOVE_SEL


def date_counter(update, context):
    """
    Initialize this module by calling /counter
    :param update: from bot API
    :param context: from bot API
    :return:
            SHOW_DATE : step 0
    """
    today = datetime.now()
    return_text = 'Cheers !\n\n'
    dates.clear()
    user = 'erikws' if update.message.from_user.username == 'sleepyforever' else update.message.from_user.username

    dates.append(fetch_item_by_key(
        db_table='important_dates',
        item={'user': user}
    )[0])

    for i in dates[0]:
        date_desc = i['desc']
        date = datetime.strptime(i['date'], '%Y-%m-%d')
        months = relativedelta(today, date).years * 12 + relativedelta(today, date).months
        days = (today - date).days
        return_text += f'{months} months or {days} days since {date_desc} \n'

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'❤❤❤❤❤ Daily Summary {datetime.now().strftime("%Y-%m-%d")} ❤❤❤❤❤'
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'{return_text}\n'
             'press /end to end this inquiry\n'
             'reply "add" to insert new date\n'
             'reply "remove" to remove date record'
    )
    return SHOW_DATE
