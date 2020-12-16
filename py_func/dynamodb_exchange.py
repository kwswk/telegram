from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')


def insert_item():
    table = dynamodb.Table('account')
    table.put_item(
        Item={
            'card_no': '4255360025489789',
            'bank': 'MOX',
            'asso': 'VISA',
            'card_type': 'ATM',
            'cycle_date': 5,
            'expiry_date': '2023-12-01',
            'limit': '999999',
            'nature': 'debit',
        }
    )


def fetch_item_by_key():
    table = dynamodb.Table('account')
    response = table.get_item(
        Key={
            'bank': 'BOCHK',
            'card_no': '5500123455551111',
        }
    )
    item = response['Item']
    print(item)


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


def delete_item():
    table = dynamodb.Table('account')
    table.delete_item(
        Key={
            'bank': 'BOCHK',
            'card_no': '5500123455551111',
        }
    )


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


def scan():
    table = dynamodb.Table('campaign')
    response = table.scan(
        FilterExpression=Attr('min_spend_all').gt(10)  # var.nest.eq('A') < support nested json
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
