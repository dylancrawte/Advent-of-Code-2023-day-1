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
        
        # Write the result to a new file
        with open('/tmp/output.txt', 'w') as file:
            file.write(f"{total_sum}\n")
        
        # Upload the new file to S3
        logger.info(f"Attempting to upload output to {output_key} in {bucket_name}")
        s3.upload_file('/tmp/output.txt', bucket_name, output_key)
        
        return {
            'statusCode': 200,
            'body': 'File processed and uploaded successfully'
        }
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'An error occurred: {str(e)}'
        }
