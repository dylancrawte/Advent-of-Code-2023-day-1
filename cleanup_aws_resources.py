import boto3

def cleanup_resources():
    # Initialize AWS clients
    s3 = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    iam = boto3.client('iam')

    # Delete S3 bucket
    bucket_name = 'advent-of-code-day'
    try:
        s3.head_bucket(Bucket=bucket_name)
        # Bucket exists, delete its contents and then the bucket
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
        s3.delete_bucket(Bucket=bucket_name)
        print(f"Deleted S3 bucket: {bucket_name}")
    except s3.exceptions.NoSuchBucket:
        print(f"S3 bucket {bucket_name} does not exist. Skipping.")
    except Exception as e:
        print(f"Error deleting S3 bucket: {str(e)}")

    # Delete Lambda function
    function_name = 'advent_of_code_day1'
    try:
        lambda_client.delete_function(FunctionName=function_name)
        print(f"Deleted Lambda function: {function_name}")
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Lambda function {function_name} does not exist. Skipping.")
    except Exception as e:
        print(f"Error deleting Lambda function: {str(e)}")

    # Delete IAM role
    role_name = 'lambda_exec_role'
    try:
        # Detach policies from the role
        attached_policies = iam.list_attached_role_policies(RoleName=role_name)
        for policy in attached_policies.get('AttachedPolicies', []):
            iam.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])
        
        # Delete the role
        iam.delete_role(RoleName=role_name)
        print(f"Deleted IAM role: {role_name}")
    except iam.exceptions.NoSuchEntityException:
        print(f"IAM role {role_name} does not exist. Skipping.")
    except Exception as e:
        print(f"Error deleting IAM role: {str(e)}")

    # Delete IAM policy
    policy_name = 'lambda_exec_role'
    try:
        # List all versions of the policy
        versions = iam.list_policy_versions(PolicyArn=f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:policy/{policy_name}")
        
        # Delete all non-default versions
        for version in versions['Versions']:
            if not version['IsDefaultVersion']:
                iam.delete_policy_version(PolicyArn=f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:policy/{policy_name}", 
                                          VersionId=version['VersionId'])
        
        # Delete the policy
        iam.delete_policy(PolicyArn=f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:policy/{policy_name}")
        print(f"Deleted IAM policy: {policy_name}")
    except iam.exceptions.NoSuchEntityException:
        print(f"IAM policy {policy_name} does not exist. Skipping.")
    except Exception as e:
        print(f"Error deleting IAM policy: {str(e)}")

if __name__ == "__main__":
    cleanup_resources()