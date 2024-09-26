import boto3
import os
import time
import logging
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(filename='athena_debug.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def run_athena_query(query, database, s3_output):
    client = boto3.client('athena')
    
    try:
        # Start the query execution
        response = client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': s3_output}
        )
        
        query_execution_id = response['QueryExecutionId']
        logger.info(f"Started query execution with ID: {query_execution_id}")
        
        # Wait for the query to complete
        while True:
            response = client.get_query_execution(QueryExecutionId=query_execution_id)
            state = response['QueryExecution']['Status']['State']
            
            if state == 'SUCCEEDED':
                logger.info(f"Query succeeded: {query_execution_id}")
                return state, query_execution_id
            elif state in ['FAILED', 'CANCELLED']:
                reason = response['QueryExecution']['Status'].get('StateChangeReason', 'No reason provided')
                logger.error(f"Query {state.lower()}: {query_execution_id}. Reason: {reason}")
                return state, query_execution_id
            
            logger.info(f"Query is still running. Current state: {state}")
            time.sleep(5)  # Wait for 5 seconds before checking again
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException':
            logger.error("Access Denied: Insufficient permissions to execute Athena query.")
            logger.error("Please ensure your IAM role has the 'athena:StartQueryExecution' permission.")
            return 'FAILED', None
        else:
            logger.error(f"AWS Error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise

def list_tables(database):
    client = boto3.client('athena')
    try:
        response = client.list_table_metadata(
            CatalogName='AwsDataCatalog',
            DatabaseName=database
        )
        tables = [table['Name'] for table in response['TableMetadataList']]
        logger.info(f"Tables in database {database}: {', '.join(tables)}")
        return tables
    except ClientError as e:
        logger.error(f"Error listing tables: {str(e)}")
        raise

def main():
    database = 'default'  # or your specific database name
    s3_output = 's3://your-bucket/athena-results/'  # replace with your S3 bucket

    # Create table query
    create_table_query = """
    CREATE EXTERNAL TABLE IF NOT EXISTS user_data (
        user_id STRING,
        username STRING,
        email STRING,
        registration_date DATE,
        last_login TIMESTAMP,
        age INT,
        is_active BOOLEAN
    )
    ROW FORMAT DELIMITED
    FIELDS TERMINATED BY ','
    STORED AS TEXTFILE
    LOCATION 's3://your-input-bucket/user-data/'
    """

    logger.info("Creating Athena table...")
    state, query_id = run_athena_query(create_table_query, database, s3_output)
    if state != 'SUCCEEDED':
        if query_id is None:
            logger.error("Failed to start query execution. Check your AWS permissions.")
        else:
            logger.error(f"Failed to create table. Query ID: {query_id}")
        return

    logger.info("Listing tables in the database...")
    tables = list_tables(database)
    if 'your_table_name' not in tables:
        logger.error("The table was not created successfully")
        return

    # Your analysis query
    analysis_query = "SELECT * FROM your_table_name LIMIT 10"

    logger.info("Running analysis query...")
    state, query_id = run_athena_query(analysis_query, database, s3_output)
    if state == 'SUCCEEDED':
        logger.info("Analysis query completed successfully")
    else:
        logger.error("Analysis query failed")

if __name__ == "__main__":
    main()