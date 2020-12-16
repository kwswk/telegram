from datetime import datetime

from dateutil.relativedelta import relativedelta


# Periodic reminder
def date_counter(update, context):
    today = datetime.now()
    anniversary = datetime(2019, 9, 6)
    meet_date = datetime(2019, 5, 23)
    first_date = datetime(2019, 6, 9)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'❤❤❤❤❤ Daily Summary {datetime.now().strftime("%Y-%m-%d")} ❤❤❤❤❤'
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Happy {(today - anniversary).days} Days!\n'
             f'{relativedelta(today, meet_date).years * 12 + relativedelta(today, meet_date).months} '
             f'months since first chat \n'
             f'{relativedelta(today, first_date).years * 12 + relativedelta(today, first_date).months} '
             f'months since first date \n'
             f'{relativedelta(today, anniversary).years * 12 + relativedelta(today, anniversary).months} '
             f'months since anniversary '
    )