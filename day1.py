import boto3
import os

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = 'advent-of-code-day'
    input_key = 'input.txt'
    output_key = 'output.txt'
    
    # Download the file from S3
    s3.download_file(bucket_name, input_key, '/tmp/input.txt')
    
    total = []


    with open('/tmp/input.txt', 'r') as file: #opens the file
        for line in file: #for each line in the file
            digits = [char for char in line if char.isdigit()] #iterates through each character, adds any digits to list
            first_digit = digits[0] 
            last_digit = digits[-1]
            number = int(first_digit + last_digit) #concatenates the first and last digit
            total.append(number) #appends to total list

    total_sum = sum(total) # calculate the sum of all numbers in the list
    print(total_sum)
    
    # Write the result to a new file
    with open('/tmp/output.txt', 'w') as file:
        file.write(f"{total_sum}\n") # write the sum to the file
    
    # Upload the new file to S3
    s3.upload_file('/tmp/output.txt', bucket_name, output_key)
    
    return {
        'statusCode': 200,
        'body': 'File processed and uploaded successfully'
    }

