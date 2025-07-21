import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    print("=== EVENT RECEIVED ===")
    print(json.dumps(event, indent=2))

    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('processed-data')  # Replace with actual table name

    try:
        bucket = event['detail']['bucket']['name']
        key = event['detail']['object']['key']
        print(f"Reading file from S3: bucket={bucket}, key={key}")
    except Exception as e:
        print(f"[ERROR] Could not extract bucket/key from event: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid event structure.')
        }

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        lines = content.splitlines()
        print(f"Total lines in file: {len(lines)}")
    except Exception as e:
        print(f"[ERROR] Failed to read file from S3: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error reading file from S3.')
        }

    success_count = 0
    failure_count = 0

    for line in lines:
        try:
            data = json.loads(line)
            data['date'] = datetime.utcnow().date().isoformat()
            print(f"Parsed data: {data}")
            response = table.put_item(Item=data)
            print("DynamoDB put_item response:", response)
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to process line: {line}")
            print(f"[REASON] {e}")
            failure_count += 1

    print(f"Successfully inserted: {success_count}, Failed: {failure_count}")

    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed file. Inserted: {success_count}, Failed: {failure_count}')
    }

