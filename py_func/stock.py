import requests


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
