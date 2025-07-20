import json
import boto3

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    
    table = dynamodb.Table('processed-data')  # Replace with actual table name

    # Get bucket and file info from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Read file content
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8')
    lines = content.splitlines()

    for line in lines:
        data = json.loads(line)  # or parse CSV if it's a CSV file
        table.put_item(Item=data)

    return {
        'statusCode': 200,
        'body': json.dumps('File processed and data stored in DynamoDB.')
    }
