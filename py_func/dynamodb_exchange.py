import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')


def insert_item(db_table: str, item: dict):
    """
    Insert items to dynamodb db table
    :param db_table: NOSQL table to be appended
    :param item: data row in dict format
    :return: no return
    """
    table = dynamodb.Table(db_table)
    table.put_item(Item=item)


def fetch_item_by_key(db_table: str, item: dict):
    """
    Extract data from dynamodb table
    :param db_table: NOSQL table to be appended
    :param item: key and eqv value to be extracted
    :return: list of related row in dict format
    """
    lst_result = list()
    table = dynamodb.Table(db_table)

    for k, v in item.items():
        response = table.query(KeyConditionExpression=Key(k).eq(v))
        lst_result.append(response['Items'])

    return lst_result


def delete_item(db_table: str, item: dict):
    """
    Remove item by key in dynamodb table
    :param db_table: Target table
    :param item: dict of keys to be removed (user + date)
    :return: None
    """
    table = dynamodb.Table(db_table)
    table.delete_item(Key=item)


def batch_process_items(db_table: str, items: list, keys: list, method='insert'):
    table = dynamodb.Table(db_table)
    with table.batch_writer(overwrite_by_pkeys=keys) as batch:
        for item in items:
            if method == 'insert':
                batch.put_item(Item=item)
            elif method == 'delete':
                batch.delete_item(Key=item)


def scan_db(db_table: str, key: str, cond: str, key2=None, cond2=None):
    table = dynamodb.Table(db_table)

    if cond2 is None:
        response = table.scan(
            FilterExpression=Attr(key).eq(cond)
        )
    else:
        response = table.scan(
            FilterExpression=Attr(key).eq(cond) & Attr(key2).eq(cond2)
        )

    items = response['Items']

    return items


def update_table(db_table: str, keys: dict, items=None):
    table = dynamodb.Table(db_table)
    table.update_item(
        Key=keys,
        UpdateExpression='SET load_date = :val1',
        ExpressionAttributeValues={
            ':val1': '2021-01-02'
        }
    )


def create_table():
    # Create the DynamoDB table. # Key == # in Definition
    table = dynamodb.create_table(
        TableName='campaign',
        KeySchema=[
            {
                'AttributeName': 'bank',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'start_date',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'bank',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'start_date',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists.
    # table.meta.client.get_waiter('table_exists').wait(TableName='users')


def query():
    table = dynamodb.Table('campaign')
    response = table.query(
        KeyConditionExpression=Key('bank').eq('BOCHK') & Key('start_date').gt('2020-10-01')
    )
    items = response['Items']
    print(items)


def delete_table():
    table = dynamodb.Table('campaign')
    table.delete()




