import boto3
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = 'advent-of-code-day'
    input_key = 'input.txt'
    output_key = 'output.txt'
    
    try:
        # Download the file from S3
        logger.info(f"Attempting to download {input_key} from {bucket_name}")
        s3.download_file(bucket_name, input_key, '/tmp/input.txt')
        
        total = []

        with open('/tmp/input.txt', 'r') as file:
            for line in file:
                digits = [char for char in line if char.isdigit()]
                if digits:  # Check if there are any digits in the line
                    first_digit = digits[0] 
                    last_digit = digits[-1]
                    number = int(first_digit + last_digit)
                    total.append(number)

        total_sum = sum(total)
        logger.info(f"Calculated sum: {total_sum}")
        
        # Write the result directly to S3
        logger.info(f"Attempting to write output to {output_key} in {bucket_name}")
        s3.put_object(Bucket=bucket_name, Key=output_key, Body=str(total_sum))
        
        return {
            'statusCode': 200,
            'body': 'File processed and result uploaded successfully'
        }
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'An error occurred: {str(e)}'
        }
