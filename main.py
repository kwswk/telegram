import requests


def telegram_bot_sendtext(bot_message):
    bot_token = '1460342157:AAH26oIP5bwvL6SMgx3lE4BsiQLnAiidGQ8'
    bot_chatID = '68096939'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()


test = telegram_bot_sendtext("hallo kWs")
print(test)