from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago
import boto3
import os
import config  # Import configuration variables
import subprocess

# Function to check if the file exists in the S3 bucket
def check_if_file_exists(**kwargs):
    session = boto3.Session(
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_KEY
    )

    # Create an S3 client
    s3_client = session.client('s3')

    bucket_name = config.S3_BUCKET_NAME
    file_name = config.S3_FILE_NAME 

    try:
        # Check if the file exists in the bucket
        s3_client.head_object(Bucket=bucket_name, Key=file_name)
        print(f"File {file_name} found in bucket {bucket_name}")
    except Exception as e:
        raise ValueError(f"File {file_name} not found in bucket {bucket_name}")

# Function to download the file from S3 using boto3
def download_file_from_s3(**kwargs):
    session = boto3.Session(
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_KEY
    )

    # Create an S3 client
    s3_client = session.client('s3')
    bucket_name = config.S3_BUCKET_NAME
    file_name = config.S3_FILE_NAME 
    download_path =  config.LOCAL_REPO_PATH + file_name

    directory = os.path.dirname(download_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory {directory}") 
    #     try:
    #         repo_url = config.REPO_URL  # Make sure to define REPO_URL in your config
    #         ssh_key_path = config.SSH_KEY_PATH  # Path to SSH key in config
    #         user_id = config.GIT_USER_ID  # User ID for Git in config
            
    # # Set the GIT_SSH_COMMAND to use the specified SSH key
    #         env = os.environ.copy()
    #         env["GIT_SSH_COMMAND"] = f"ssh -i {ssh_key_path} -o IdentitiesOnly=yes"

    #         # Run the git clone command
    #         subprocess.run(
    #             ["git", "clone", f"git@github.com:{user_id}/{repo_url.split('/')[-1].replace('.git', '')}.git", directory],
    #             check=True,
    #             env=env
    #         )
    #         print(f"Cloned repository from {repo_url} into {directory}")

    #     except subprocess.CalledProcessError as e:
    #         print(f"Error occurred while cloning the repository: {e}")
    #         return  # Exit if cloning fails


    # Download the file
    s3_client.download_file(bucket_name, file_name, download_path)
    print(f"Downloaded {file_name} from bucket {bucket_name} to {download_path}")


# Function for preprocessing (can be extended based on requirements)
def preprocess_data(**kwargs):
    # Simulate a preprocessing step
    raw_file = os.path.join(config.LOCAL_REPO_PATH, config.S3_FILE_NAME)
    processed_file = os.path.join(config.LOCAL_REPO_PATH, config.PREPROCESSED_FILE_NAME)
    
    # Simple preprocessing task - copying the file with a different name
    os.system(f"cp {raw_file} {processed_file}")
    print(f"Preprocessed {raw_file} to {processed_file}")

# Default args for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'retries': 1,
}

# Define the DAG
dag = DAG(
    's3_to_github_lfs_boto3_with_check',
    default_args=default_args,
    description='Check for S3 file, download, preprocess, and run DVC commands',
    schedule_interval=None,
)

# Task to check if the data file exists in S3
check_if_data_file_arrived = PythonOperator(
    task_id='check_if_data_file_arrived',
    python_callable=check_if_file_exists,
    dag=dag,
)

# Task to download the file from S3 using boto3
download_file = PythonOperator(
    task_id='download_file',
    python_callable=download_file_from_s3,
    dag=dag,
)

# Task for preprocessing the data
preprocess_task = PythonOperator(
    task_id='preprocess_task',
    python_callable=preprocess_data,
    dag=dag,
)

# Task to run DVC commands to track the data version
dvc_commands_task = BashOperator(
    task_id='dvc_commands_task',
    bash_command=f"""
        cd {config.LOCAL_REPO_PATH} &&
        dvc init -f &&
        dvc remote add -f -d myremote s3://{config.S3_BUCKET_NAME}/dvc-store &&
        git config --global --add safe.directory /opt/airflow/data-version-01 &&
        git config --global user.email "anazjbh@gmail.com" &&
        git config --global user.name "Anaz Jaleel" &&
        dvc add {config.PREPROCESSED_FILE_NAME} &&
        git add {config.PREPROCESSED_FILE_NAME}.dvc .gitignore &&
        git commit -m "Add preprocessed data to DVC" &&
        git push -f origin &&
        dvc commit && 
        push
    """,
    dag=dag,
)

#bash_command='cd /opt/airflow/$DATA_REPO_NAME && dvc init -f && dvc remote add -f-d myremote s3://$53_BUCKET_NAME/dvc-store && git config --global user.email "test@ickn.com" && git config --global user.name "Demo User" && dvc add *.csv * parquet && git add *.dvc gitignore && git commit -m "added transformed file" && git push -f origin && dvc commit && push

# Set up task dependencies
check_if_data_file_arrived >> download_file >> preprocess_task >> dvc_commands_task

