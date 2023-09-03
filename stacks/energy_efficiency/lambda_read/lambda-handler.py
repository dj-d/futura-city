# TODO: Add logger

import os
import boto3
import pymysql
from typing import Union, Optional


def handler(event, context):
    secret = get_secret()

    # Connect to database
    try:
        conn = pymysql.connect(
            host=secret["host"],
            port=secret["port"],
            user=secret["username"],
            password=secret["password"],
            database=secret["dbname"]
        )

        print('Connected to database')
    except pymysql.MySQLError as e:
        # print(f'Error: {e}')
        # raise e

        return make_response(
            status_code=500,
            error=e
        )

    # Read data
    try:
        with conn.cursor() as cur:
            sql = 'SELECT * FROM energy_efficiency'

            cur.execute(sql)
            rows = cur.fetchall()
            rows = list(rows)

            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'name': row[1]
                })
    except pymysql.MySQLError as e:
        # print(f'Error: {e}')
        # raise e

        return make_response(
            status_code=500,
            error=e
        )

    # Close connection
    try:
        conn.close()
        print('Closed connection')
    except pymysql.MySQLError as e:
        # print(f'Error: {e}')
        # raise e

        return make_response(
            status_code=500,
            error=e
        )

    return make_response(
        status_code=200,
        body=results
    )


def get_secret():
    # Get environment variables
    db_secret_arn = os.environ['DB_SECRET_ARN']

    # Get secret from Secrets Manager
    client = boto3.client('secretsmanager')
    get_secret_value_response = client.get_secret_value(
        SecretId=db_secret_arn
    )
    secret = eval(get_secret_value_response['SecretString'])

    return secret


def make_response(status_code: int, body: Union[dict, list] = None, error: Optional[pymysql.MySQLError] = None) -> dict:
    if error is not None:
        print(f'etype: {type(error)}')
        code, message = error.args
        return {
            'statusCode': status_code,
            'body': {
                'error_code': code,
                'error_message': message
            }
        }

    return {
        'statusCode': status_code,
        'body': body
    }
