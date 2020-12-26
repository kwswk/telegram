import requests


def quote_price(market, code):
    """
    calling Alpha Vantage API
    :param market: US or HK
    :param code: Stock Code
    :return: Dict of price
    """

    if market != 'US':
        code = f'{code.zfill(4)}.{market}'

    url = "https://alpha-vantage.p.rapidapi.com/query"
    querystring = {"function": "GLOBAL_QUOTE", "symbol": code}

    headers = {
        'x-rapidapi-key': "5c2f24892fmsh58278fdf1cebf0fp1bb586jsndda6a2eceff8",
        'x-rapidapi-host': "alpha-vantage.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    return response.text
