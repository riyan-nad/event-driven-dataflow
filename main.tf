# -------------------------------
# 1. S3 Bucket to Upload Files
# -------------------------------
resource "aws_s3_bucket" "upload_bucket" {
  bucket = "event-driven-upload-bucket-riyan"
  force_destroy = true
}

# -------------------------------
# 2. DynamoDB Table
# -------------------------------
resource "aws_dynamodb_table" "data_table" {
  name         = "processed-data"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

# -------------------------------
# 3. IAM Role for Lambda Functions
# -------------------------------
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Attach basic Lambda and full access permissions
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_full_access" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_ses_access" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSESFullAccess"
}

# -------------------------------
# 4. Lambda Functions
# -------------------------------
data "archive_file" "process_file_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/process_file.py"
  output_path = "${path.module}/lambda/process_file.zip"
}

resource "aws_lambda_function" "process_file_lambda" {
  function_name    = "ProcessFileFunction"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "process_file.lambda_handler"
  runtime          = "python3.10"
  filename         = data.archive_file.process_file_lambda_zip.output_path
  source_code_hash = data.archive_file.process_file_lambda_zip.output_base64sha256
  timeout          = 30

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_full_access,
    aws_iam_role_policy_attachment.lambda_s3_access
  ]
}

data "archive_file" "report_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/generate_report.py"
  output_path = "${path.module}/lambda/generate_report.zip"
}

resource "aws_lambda_function" "generate_report_lambda" {
  function_name    = "GenerateReportFunction"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "generate_report.lambda_handler"
  runtime          = "python3.10"
  filename         = data.archive_file.report_lambda_zip.output_path
  source_code_hash = data.archive_file.report_lambda_zip.output_base64sha256
  timeout          = 60

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_full_access,
    aws_iam_role_policy_attachment.lambda_ses_access
  ]
}

# -------------------------------
# 5. S3 Trigger via EventBridge
# -------------------------------
resource "aws_cloudwatch_event_rule" "s3_upload_event" {
  name = "S3UploadEventRule"
  event_pattern = jsonencode({
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {
        "name": [aws_s3_bucket.upload_bucket.bucket]
      },
      "object": {
        "key": [{"exists": true}]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "s3_upload_target" {
  rule = aws_cloudwatch_event_rule.s3_upload_event.name
  arn  = aws_lambda_function.process_file_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge_to_invoke_lambda1" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_file_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.s3_upload_event.arn
}

# -------------------------------
# 6. CloudWatch Scheduled Trigger for Daily Report
# -------------------------------
resource "aws_cloudwatch_event_rule" "daily_report_schedule" {
  name                = "DailyReportTrigger"
  schedule_expression = "cron(50 10 * * ? *)" # 3:10 PM IST = 9:40 AM UTC
}

resource "aws_cloudwatch_event_target" "daily_report_target" {
  rule = aws_cloudwatch_event_rule.daily_report_schedule.name
  arn  = aws_lambda_function.generate_report_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge_to_invoke_lambda2" {
  statement_id  = "AllowScheduledExecution"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.generate_report_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_report_schedule.arn
}
