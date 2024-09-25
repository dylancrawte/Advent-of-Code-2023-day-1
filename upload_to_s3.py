import boto3
import sys

def upload_file_to_s3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return False
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python upload_to_s3.py <file_name> <bucket_name>")
        sys.exit(1)

    file_name = sys.argv[1]
    bucket_name = sys.argv[2]

    if upload_file_to_s3(file_name, bucket_name):
        print(f"Successfully uploaded {file_name} to {bucket_name}")
    else:
        print(f"Failed to upload {file_name} to {bucket_name}")
        sys.exit(1)