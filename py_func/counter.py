from datetime import datetime
from dateutil.relativedelta import relativedelta

import re

from .dynamodb_exchange import insert_item, fetch_item_by_key

# Global vars:
SHOW_DATE, ADD_DATE, ADD_DESC, ADD_DONE, REMOVE_DATE = range(5)
item_date = dict()


def add_dates_handler(update, context):
    if re.match('(?i)add', update.message.text):
        item_date['user'] = update.message.chat.username
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


def date_counter(update, context):
    """Periodic reminder"""
    today = datetime.now()
    return_text = 'Cheers !\n'

    dates = fetch_item_by_key(db_table='important_dates', item={'user': update.message.chat.username})
    for i in dates[0]:
        date_desc = i['desc']
        date = datetime.strptime(i['date'], '%Y-%m-%d')
        months = relativedelta(today, date).years * 12 + relativedelta(today, date).months
        return_text += f'{months} months since {date_desc} \n'
    print(dates)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'❤❤❤❤❤ Daily Summary {datetime.now().strftime("%Y-%m-%d")} ❤❤❤❤❤'
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'{return_text}\n'
             'press /end to end this inquiry\n'
             'reply "add" to insert new date\n'
        # 'reply "remove" to remove date record'
    )
    return SHOW_DATE

# def counter(update, context):
#     """/start"""
#     context.bot.send_message(chat_id=update.effective_chat.id, text='Hi BB, this is our AI reminder')
#     # updater.job_queue.run_repeating(date_counter, context=update.effective_chat.id, interval=86400,  first=0.1)
