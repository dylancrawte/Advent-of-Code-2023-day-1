import boto3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_athena_database(database_name):
    # Create Athena client
    athena_client = boto3.client('athena')
    
    try:
        # Delete the database
        response = athena_client.delete_data_catalog_database(
            CatalogName='AwsDataCatalog',
            DatabaseName=database_name
        )
        
        logger.info(f"Successfully deleted Athena database: {database_name}")
        return True
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    
    return False

if __name__ == "__main__":
    # Replace 'your_database_name' with the actual name of your Athena database
    database_name = 'your_database_name'
    delete_athena_database(database_name)