import boto3
import os
import time

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
        results = get_query_results(query_execution_id)
        # Format results as Markdown table
        markdown_table = "| " + " | ".join(results['ResultSet']['Rows'][0]['Data']) + " |\n"
        markdown_table += "|" + "---|" * len(results['ResultSet']['Rows'][0]['Data']) + "\n"

        for row in results['ResultSet']['Rows'][1:]:
            markdown_table += "| " + " | ".join([data.get('VarCharValue', '') for data in row['Data']]) + " |\n"

        # Write results to query_results.md
        with open('query_results.md', 'w') as f:
            f.write("# Athena Query Results\n\n")
            f.write(markdown_table)

        print("Query results have been written to query_results.md")
        return {
            'statusCode': 200,
            'body': results['ResultSet']['Rows']
        }
    else:
        return {
            'statusCode': 500,
            'body': f"Query failed with status: {status}"
        }

def get_query_results(query_execution_id):
    athena_client = boto3.client('athena')
    
    while True:
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        state = response['QueryExecution']['Status']['State']
        
        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        
        time.sleep(5)
    
    if state == 'SUCCEEDED':
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        return results
    else:
        raise Exception(f"Query failed with state: {state}")