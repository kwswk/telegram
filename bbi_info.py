import requests
import json


def get_bbi_info(route: object) -> dict:
    direction = ['F', 'B']
    bbi_info = list()
    for i in direction:
        conn = requests.get(f'http://www.kmb.hk/ajax/BBI/get_BBI2-en.php?routeno={route}&bound={i}')
        bbi_raw = json.loads(conn.text)
        bbi_info.append(bbi_raw)

    bbi_dict = {i['bus_arr'][0]['dest']: i['Records'] for i in bbi_info}

    return bbi_dict