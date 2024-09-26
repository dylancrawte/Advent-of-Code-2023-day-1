provider "aws" {
  region = "us-west-2"
}

resource "aws_s3_bucket" "my_bucket" {
  bucket = "advent-of-code-day"
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",  // Add this line
  ]
}

locals {
  sql_script = <<EOF
-- Create an external table that points to the S3 bucket
CREATE EXTERNAL TABLE IF NOT EXISTS advent_of_code_output (
    line STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3://advent-of-code-day/';

-- Query the data from the external table
SELECT line
FROM advent_of_code_output;
EOF
}

resource "aws_lambda_function" "day1_lambda" {
  function_name    = "advent-of-code-2023-day1"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "day1.lambda_handler"
  runtime          = "python3.8"
  filename         = data.archive_file.day1_zip.output_path
  source_code_hash = data.archive_file.day1_zip.output_base64sha256

  environment {
    variables = {
      S3_BUCKET     = aws_s3_bucket.my_bucket.bucket
      SQL_SCRIPT    = local.sql_script
      ATHENA_DB     = aws_athena_database.advent_database.name
      ATHENA_OUTPUT = "s3://${aws_s3_bucket.my_bucket.bucket}/athena_results/"
    }
  }
}

resource "aws_lambda_function" "main_lambda" {
  function_name    = "advent-of-code-2023-main"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "lambda_athena.lambda_handler"
  runtime          = "python3.8"
  filename         = data.archive_file.main_lambda_zip.output_path
  source_code_hash = data.archive_file.main_lambda_zip.output_base64sha256

  environment {
    variables = {
      S3_BUCKET     = aws_s3_bucket.my_bucket.bucket
      SQL_SCRIPT    = local.sql_script
      ATHENA_DB     = aws_athena_database.advent_database.name
      ATHENA_OUTPUT = "s3://${aws_s3_bucket.my_bucket.bucket}/athena_results/"
    }
  }
}

data "archive_file" "day1_zip" {
  type        = "zip"
  source_file = "${path.module}/day1.py"
  output_path = "${path.module}/day1_lambda.zip"
}

data "archive_file" "main_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_athena.py"
  output_path = "${path.module}/main_lambda.zip"
}

output "s3_bucket_name" {
  value = aws_s3_bucket.my_bucket.bucket
}

output "day1_lambda_function_name" {
  value = aws_lambda_function.day1_lambda.function_name
}

output "main_lambda_function_name" {
  value = aws_lambda_function.main_lambda.function_name
}

resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "lambda_s3_policy"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:HeadObject",
          "s3:GetBucketAcl",
          "s3:CreateBucket",
          "s3:GetBucketCORS",
          "s3:PutBucketCORS",
          "s3:GetBucketWebsite"
        ]
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.my_bucket.bucket}",
          "arn:aws:s3:::${aws_s3_bucket.my_bucket.bucket}/*"
        ]
      }
    ]
  })
}

// Add IAM permissions for Athena and Glue
resource "aws_iam_role_policy_attachment" "lambda_athena_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonAthenaFullAccess"
}

resource "aws_athena_workgroup" "advent_workgroup" {
  name = "advent_workgroup"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.my_bucket.bucket}/athena_results/"
    }
  }
}

resource "aws_athena_database" "advent_database" {
  name   = "advent_database"
  bucket = aws_s3_bucket.my_bucket.bucket
}

resource "aws_athena_named_query" "example_query" {
  name      = "example_query"
  workgroup = aws_athena_workgroup.advent_workgroup.name
  database  = aws_athena_database.advent_database.name
  query     = <<EOF
CREATE EXTERNAL TABLE IF NOT EXISTS advent_table (
  column1 int
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://${aws_s3_bucket.my_bucket.bucket}/';

SELECT * FROM advent_table LIMIT 10;
EOF

}

resource "null_resource" "cleanup_script" {
  provisioner "local-exec" {
    command = <<-EOT
      cat <<EOF > cleanup.sh
      #!/bin/bash
      set -e

      # Delete S3 bucket
      aws s3 rb s3://${aws_s3_bucket.my_bucket.bucket} --force

      # Delete Lambda functions
      aws lambda delete-function --function-name ${aws_lambda_function.day1_lambda.function_name}
      aws lambda delete-function --function-name ${aws_lambda_function.main_lambda.function_name}

      # Delete IAM role
      aws iam delete-role --role-name ${aws_iam_role.lambda_exec_role.name}

      # Delete Athena workgroup and database
      aws athena delete-work-group --work-group ${aws_athena_workgroup.advent_workgroup.name} --recursive-delete-option
      aws athena delete-data-catalog --name ${aws_athena_database.advent_database.name}
    EOF
      chmod +x cleanup.sh
    EOT
  }
}

output "cleanup_script_path" {
  value = "${path.module}/cleanup.sh"
}
