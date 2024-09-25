import boto3
import os
import logging
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = 'advent-of-code-day'
    input_key = 'input.txt'
    output_key = 'output.txt'
    
    try:
        # Check if the bucket exists
        try:
            s3.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} exists and is accessible")
        except ClientError as e:
            logger.error(f"Bucket {bucket_name} is not accessible: {str(e)}")
            raise

        # Download the file from S3
        logger.info(f"Attempting to download {input_key} from {bucket_name}")
        try:
            s3.download_file(bucket_name, input_key, '/tmp/input.txt')
            logger.info(f"Successfully downloaded {input_key}")
        except ClientError as e:
            logger.error(f"Failed to download {input_key}: {str(e)}")
            raise

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
        try:
            response = s3.put_object(Bucket=bucket_name, Key=output_key, Body=str(total_sum))
            logger.info(f"Put object response: {response}")
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                raise Exception(f"Failed to upload file. Response: {response}")
            logger.info(f"Successfully wrote {output_key} to {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to write {output_key}: {str(e)}")
            raise

        return {
            'statusCode': 200,
            'body': 'File processed and result uploaded successfully'
        }
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': f'An error occurred: {str(e)}'
        }
