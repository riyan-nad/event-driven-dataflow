import boto3
import json
from datetime import datetime
import os

region = os.environ.get("AWS_REGION", "us-east-1")

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb', region_name=region)
    ses = boto3.client('ses', region_name=region)
    
    table = dynamodb.Table('processed-data')

    response = table.scan()
    items = response.get('Items', [])

    report_content = f"Daily Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    report_content += f"Total records: {len(items)}\n\n"

    for item in items:
        report_content += json.dumps(item) + '\n'

    # Send email via SES
    ses.send_email(
        Source='riyannadersha@gmail.com',
        Destination={'ToAddresses': ['rinoosnadersha@gmail.com']},
        Message={
            'Subject': {'Data': 'Daily Report'},
            'Body': {'Text': {'Data': report_content}}
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Report generated and sent via email.')
    }
