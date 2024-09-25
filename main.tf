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

resource "aws_lambda_function" "my_lambda" {
  function_name = "advent-of-code-2023"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "day1.lambda_handler"  
  runtime       = "python3.8"
  filename      = "day1.zip"
  source_code_hash = filebase64sha256("day1.zip")
}

output "s3_bucket_name" {
  value = aws_s3_bucket.my_bucket.bucket
}

output "lambda_function_name" {
  value = aws_lambda_function.my_lambda.function_name
}


// Add this new resource
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
          "s3:HeadObject"
        ]
        Resource = [
          "arn:aws:s3:::advent-of-code-day",
          "arn:aws:s3:::advent-of-code-day/*"
        ]
      }
    ]
  })
}

