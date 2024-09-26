-- Create an external table that points to the S3 bucket
CREATE EXTERNAL TABLE IF NOT EXISTS advent_of_code_output (
    line STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3://advent-of-code-day/';

-- Query the data from the external table
SELECT line
FROM advent_of_code_output;
