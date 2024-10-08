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
    
    # Validate S3 output location
    if not s3_output.startswith('s3://'):
        logger.error(f"Invalid S3 output location: {s3_output}. Must start with 's3://'")
        return 'FAILED', None

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
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        if error_code == 'InvalidRequestException':
            logger.error(f"Invalid request: {error_message}")
            logger.error("Please check that your S3 output location is correct and in the same region as your Athena query.")
        elif error_code == 'AccessDeniedException':
            logger.error("Access Denied: Insufficient permissions to execute Athena query.")
            logger.error("Please ensure your IAM role has the necessary permissions for Athena and S3.")
        else:
            logger.error(f"AWS Error: {error_code} - {error_message}")
        return 'FAILED', None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return 'FAILED', None

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

def create_database(database_name, s3_output):
    client = boto3.client('athena')
    create_db_query = f"CREATE DATABASE IF NOT EXISTS {database_name}"
    
    logger.info(f"Creating database: {database_name}")
    logger.info(f"Using S3 output: {s3_output}")
    logger.info(f"Query: {create_db_query}")
    
    state, query_id = run_athena_query(create_db_query, 'default', s3_output)
    
    logger.info(f"Query execution state: {state}")
    logger.info(f"Query execution ID: {query_id}")
    
    if state == 'SUCCEEDED':
        logger.info(f"Database '{database_name}' created successfully")
        return True
    else:
        logger.error(f"Failed to create database '{database_name}'. Query ID: {query_id}")
        return False

def main():
    database = 'advent_of_code_db'  # New database name
    s3_output = 's3://advent-of-code-day/query_results/'  # S3 bucket for query results

    # Create the database
    if not create_database(database, s3_output):
        return

    # Updated create table query for a single column, specifically for output.txt
    create_table_query = """
    CREATE EXTERNAL TABLE IF NOT EXISTS output_data (
        value STRING
    )
    ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\n'
    STORED AS TEXTFILE
    LOCATION 's3://advent-of-code-day/'
    TBLPROPERTIES (
        'skip.header.line.count'='0',
        'serialization.null.format'='',
        'input.format'='org.apache.hadoop.mapred.TextInputFormat',
        'input.regex'='(.*)',
        'input.filename'='output.txt'
    )
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
    if 'output_data' not in tables:
        logger.error("The table was not created successfully")
        return

    # Updated analysis query
    analysis_query = "SELECT value FROM output_data LIMIT 10"

    logger.info("Running analysis query...")
    state, query_id = run_athena_query(analysis_query, database, s3_output)
    if state == 'SUCCEEDED':
        logger.info("Analysis query completed successfully")
    else:
        logger.error("Analysis query failed")

if __name__ == "__main__":
    main()