import boto3
from delete_athena_database import delete_athena_database

def cleanup_resources():
    # Initialize AWS clients
    s3 = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    iam = boto3.client('iam')
    athena = boto3.client('athena')

    # Delete S3 bucket
    bucket_name = 'advent-of-code-day'
    try:
        # Check if bucket exists
        s3.head_bucket(Bucket=bucket_name)
        
        # Empty the bucket first, including all versions and delete markers
        paginator = s3.get_paginator('list_object_versions')
        for page in paginator.paginate(Bucket=bucket_name):
            objects_to_delete = []
            for version in page.get('Versions', []):
                objects_to_delete.append({'Key': version['Key'], 'VersionId': version['VersionId']})
            for marker in page.get('DeleteMarkers', []):
                objects_to_delete.append({'Key': marker['Key'], 'VersionId': marker['VersionId']})
            
            if objects_to_delete:
                s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects_to_delete})
        
        # Now delete the empty bucket
        s3.delete_bucket(Bucket=bucket_name)
        print(f"Deleted S3 bucket: {bucket_name}")
    except s3.exceptions.NoSuchBucket:
        print(f"S3 bucket {bucket_name} does not exist. Skipping.")
    except s3.exceptions.BucketNotEmpty:
        print(f"S3 bucket {bucket_name} is not empty. Please check bucket policies and object locks.")
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
        # Remove instance profiles
        instance_profiles = iam.list_instance_profiles_for_role(RoleName=role_name)
        for profile in instance_profiles['InstanceProfiles']:
            iam.remove_role_from_instance_profile(
                InstanceProfileName=profile['InstanceProfileName'],
                RoleName=role_name
            )

        # Detach managed policies
        paginator = iam.get_paginator('list_attached_role_policies')
        for page in paginator.paginate(RoleName=role_name):
            for policy in page['AttachedPolicies']:
                iam.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])

        # Delete inline policies
        paginator = iam.get_paginator('list_role_policies')
        for page in paginator.paginate(RoleName=role_name):
            for policy_name in page['PolicyNames']:
                iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

        # Delete the role
        iam.delete_role(RoleName=role_name)
        print(f"Deleted IAM role: {role_name}")
    except iam.exceptions.NoSuchEntityException:
        print(f"IAM role {role_name} does not exist. Skipping.")
    except iam.exceptions.DeleteConflictException as e:
        print(f"IAM role {role_name} cannot be deleted due to existing resources: {str(e)}")
        print("Please check for any resources still associated with this role.")
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

    # Delete Athena workgroup
    workgroup_name = 'advent_workgroup'
    try:
        # Check if the workgroup exists
        athena.get_work_group(WorkGroup=workgroup_name)
        # If it exists, delete it
        athena.delete_work_group(WorkGroup=workgroup_name, RecursiveDeleteOption=True)
        print(f"Deleted Athena workgroup: {workgroup_name}")
    except athena.exceptions.InvalidRequestException:
        print(f"Athena workgroup {workgroup_name} does not exist. Skipping.")
    except Exception as e:
        print(f"Error deleting Athena workgroup: {str(e)}")

    # Delete Athena database
    database_name = 'advent_database'
    if delete_athena_database(database_name):
        print(f"Athena database '{database_name}' deleted successfully.")
    else:
        print(f"Failed to delete Athena database '{database_name}'.")

if __name__ == "__main__":
    cleanup_resources()