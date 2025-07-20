import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('processed-data')  # Replace with actual table name

    # Get bucket and key from EventBridge format
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']
    
    print(f"Reading file from S3: bucket={bucket}, key={key}")

    # Read file content
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8')
    lines = content.splitlines()
    
    print(f"Total lines in file: {len(lines)}")

    for line in lines:
        try:
            data = json.loads(line)
            data['date'] = datetime.utcnow().date().isoformat()
            table.put_item(Item=data)
            print(f"Inserted item: {data}")
        except Exception as e:
            print(f"Error processing line: {line} — {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('File processed and data stored in DynamoDB.')
    }
