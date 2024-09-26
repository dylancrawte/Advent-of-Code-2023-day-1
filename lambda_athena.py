import boto3
import os

def lambda_handler(event, context):
    s3_bucket = os.environ['S3_BUCKET']
    sql_script = os.environ['SQL_SCRIPT']
    athena_db = os.environ['ATHENA_DB']
    athena_output = os.environ['ATHENA_OUTPUT']

    athena_client = boto3.client('athena')

    # Execute Athena query
    response = athena_client.start_query_execution(
        QueryString=sql_script,
        QueryExecutionContext={
            'Database': athena_db
        },
        ResultConfiguration={
            'OutputLocation': athena_output
        }
    )

    # Get query execution ID
    query_execution_id = response['QueryExecutionId']

    # Wait for query to complete
    while True:
        query_status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        status = query_status['QueryExecution']['Status']['State']
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break

    # Fetch and return results
    if status == 'SUCCEEDED':
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        return {
            'statusCode': 200,
            'body': results['ResultSet']['Rows']
        }
    else:
        return {
            'statusCode': 500,
            'body': f"Query failed with status: {status}"
        }