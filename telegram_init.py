from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import replykeyboardmarkup, InlineKeyboardMarkup, InlineKeyboardButton
from bbi_info import get_bbi_info


def start(update, context):
    """/start"""
    context.bot.send_message(chat_id=update.effective_chat.id, text="hey bb, try my breast!")


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{update.message.text}")


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def bbi(update, context):
    route = context.args[0]
    bbi_dict = get_bbi_info(route)
    btn_directions = list(bbi_dict.keys())

    lst_button = list()
    for i in btn_directions:
        lst_button.append(InlineKeyboardButton(i, callback_data=str(i)))

    reply_markup = InlineKeyboardMarkup([lst_button])

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f'Rt. {route} ,, Choose Direction',
                             reply_markup=reply_markup
                             )


def bbi_reply(update, context):
    """handle BBI callback"""
    if update.callback_query.message.text.split(' ')[0] == 'Rt.':
        route = update.callback_query.message.text.split(' ')[1]
        destination = update.callback_query.data
        bbi_dict = get_bbi_info(route)[destination]
        lst_chg = [i['sec_routeno'] for i in bbi_dict]

        lst_button = list()
        for i in lst_chg:
            lst_button.append(InlineKeyboardButton(i, callback_data=str(i)))

        reply_markup = InlineKeyboardMarkup([lst_button])

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'You Can Change the following routes - Rt. {route}',
                                 reply_markup=reply_markup
                                 )
    elif update.callback_query.message.text[:35] == 'You Can Change the following routes':

        route_chosen = update.callback_query.data
        change_dir = [i['sec_dest'] for i in lst_chg if i['sec_routeno'] == route_chosen].pop
        change_dest = [i['xchange'] for i in lst_chg if i['sec_routeno'] == route_chosen].pop
        fare_detail = [i['discount_max'] for i in lst_chg if i['sec_routeno'] == route_chosen].pop

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Change {route_chosen} to {change_dir}',
                                 )
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Change Point : {change_dest}',
                                 )
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Detail : {fare_detail}',
                                 )


if __name__ == '__main__':
    updater = Updater('1460342157:AAH26oIP5bwvL6SMgx3lE4BsiQLnAiidGQ8', use_context=True)

    """add functions to dispatcher"""
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('bbi', bbi))
    dp.add_handler(CallbackQueryHandler(bbi_reply))
    # dp.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    """Unknown handler"""
    dp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
