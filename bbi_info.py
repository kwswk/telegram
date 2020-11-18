import requests
import json
from tabulate import tabulate
import pandas as pd

def get_bbi_info(route: str, direction: str) -> str:
    conn = requests.get(f'http://www.kmb.hk/ajax/BBI/get_BBI2-en.php?routeno={route}&bound={direction}')
    bbi_dict = json.loads(conn.text)

    terminus = bbi_dict['bus_arr'][0]['dest']
    bbi_detail = bbi_dict['Records']
    df_bbi = pd.DataFrame(bbi_detail)[
        ['sec_routeno',
         # 'sec_dest',
         # 'xchange',
         'discount_max'
         ]
    ].set_index('sec_routeno')
    return tabulate(df_bbi, tablefmt="pipe", headers="keys")
