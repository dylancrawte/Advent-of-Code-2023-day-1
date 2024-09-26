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
    except athena_client.exceptions.InternalServerException:
        logger.error(f"An internal error occurred while deleting the database: {database_name}")
    except athena_client.exceptions.InvalidRequestException:
        logger.error(f"Invalid request to delete database: {database_name}")
    except athena_client.exceptions.MetadataException:
        logger.error(f"A metadata error occurred while deleting the database: {database_name}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    
    return False

if __name__ == "__main__":
    # Replace 'your_database_name' with the actual name of your Athena database
    database_name = 'your_database_name'
    delete_athena_database(database_name)