from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')


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


def scan(db_table: str, item: dict):
    table = dynamodb.Table(db_table)
    response = table.scan(
        FilterExpression=Attr('min_spend_all').gt(10)  # var.nest.eq('A') < support nested json
    )
    items = response['Items']


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


def batch_insert_items():
    table = dynamodb.Table('campaign')
    with table.batch_writer(overwrite_by_pkeys=['bank', 'start_date']) as batch:
        batch.put_item(
            Item={
                'bank': 'BOCHK',
                'start_date': '2020-11-15',
                'expiry_date': '2020-12-31',
                'rebate_date': '2020-02-22',
                'card': 'Taobao',
                'rebate_type': 'gift point',
                'rebate_cap': 100,
                'rebate_ratio': Decimal('0.5'),
                'min_spend_each': 1000,
                'min_spend_all': 10000
            }
        )
        batch.put_item(
            Item={
                'bank': 'HSBC',
                'start_date': '2020-12-15',
                'expiry_date': '2021-12-31',
                'rebate_date': '2022-02-22',
                'card': 'VS',
                'rebate_type': 'gift point',
                'rebate_cap': 300,
                'rebate_ratio': Decimal('0.056'),
                'min_spend_each': 500,
                'min_spend_all': 8000
            }
        )


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


def update():
    table = dynamodb.Table('campaign')
    table.update_item(
        Key={
            'bank': 'HSBC',
            'start_date': '2020-12-15',
        },
        UpdateExpression='SET progress = :val1',
        ExpressionAttributeValues={
            ':val1': 100
        }
    )

