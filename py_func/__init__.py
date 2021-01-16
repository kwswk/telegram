from telegram.ext import ConversationHandler


def greet(update, context):
    """/hi command to pop up menu"""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi BB, this is our bot!! Press command to start\n\n "
             "/counter\t\t🤑 Trigger time machine\n\n "
             "/bbi\t\t🚌 Check Bus Interchange info\n\n"
             "/stock\t\t🤑 Track stock holdings\n\n"
             "/about_me\t\t🤖 Track stock holdings\n\n"
    )


def unknown(update, context):
    """Error handling"""
    context.bot.send_message(chat_id=update.effective_chat.id, text='Unknown Command')


def about_me(update, context):
    """Error handling"""
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open('infrastructure.png', 'rb'),
        caption="I'm AWS based, visit my code on github:\n"
                "https://github.com/kwswk/telegram\n"
    )


def conv_end(update, context):
    """/end command handler"""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'See you! Input /hi to call me again :D'
    )
    return ConversationHandler.END


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """fix layout of long list of inline buttons"""
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu
