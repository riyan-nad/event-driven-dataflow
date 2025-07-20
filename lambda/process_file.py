import json
import boto3
import os

region = os.environ.get("AWS_REGION", "us-east-1")  # fallback

def lambda_handler(event, context):
    s3 = boto3.client('s3', region_name=region)
    dynamodb = boto3.resource('dynamodb', region_name=region)
    
    table = dynamodb.Table('processed-data')

    try:
        # Get bucket and key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        lines = content.splitlines()

        for i, line in enumerate(lines):
            try:
                data = json.loads(line)
                if 'id' not in data:
                    data['id'] = f"{key}-{i}"  # Auto-generate id if missing
                table.put_item(Item=data)
            except json.JSONDecodeError:
                print(f"Line {i} is not valid JSON: {line}")
            except Exception as e:
                print(f"Failed to insert line {i}: {e}")

        return {
            'statusCode': 200,
            'body': json.dumps('File processed and data stored in DynamoDB.')
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error processing file: {str(e)}")
        }
