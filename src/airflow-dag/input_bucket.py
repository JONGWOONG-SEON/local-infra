from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.base import BaseSensorOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowSkipException
from botocore.exceptions import ClientError
from src.s3 import S3Config,S3MetaStore
from src.trigger import get_dagid_by_tag
from datetime import datetime
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from collections import defaultdict
import boto3
import os
import json

load_dotenv()

SOURCE_BUCKET = "input"
DEST_BUCKET = "result"
config = S3Config.get_env()
store = S3MetaStore(config = config)

class catch_input_bucket(BaseSensorOperator):

    def poke(self, context):
        s3 = store()    
        processed = store.load_processed_files()
        response = s3.list_objects_v2(Bucket=SOURCE_BUCKET)

        if "Contents" not in response:
            raise AirflowSkipException("Empty Bucket, Exception Task Input")

        new_files = [
            obj["Key"]
            for obj in response["Contents"]
            if obj["Key"].endswith(".csv") and obj["Key"] not in processed
        ]

        if new_files:
            context["ti"].xcom_push(key="new_files", value=new_files)
            return True
        else:
            raise AirflowSkipException("No new file, Exception Task Input")
    
def transfer_file(**context):
    keys = context["ti"].xcom_pull(key="new_files")
    s3 = store()
    processed = store.load_processed_files()
    # result_file = []
    result = defaultdict(list)

    for key in keys:
        if key in processed:
            print(f"{key} already processed.")
            continue
        else:
            local_file = f"/tmp/{os.path.basename(key)}"
            s3.download_file(SOURCE_BUCKET, key, local_file)

            base_filename = os.path.splitext(os.path.basename(key))[0]
            parts = base_filename.split("_")

            if len(parts) < 2:
                print(f"Base File Name :{base_filename} \n Invalid file format expected *_*.csv")

            kst = ZoneInfo("Asia/Seoul")
            prefix = parts[0]
            timestamp = datetime.now(kst).strftime("%Y%m%d%H%M")
            dest_key = f"{prefix}/{base_filename}_{timestamp}.csv"

            result[prefix].append(dest_key)

            s3.upload_file(local_file, DEST_BUCKET, dest_key)
            processed.add(key)
            print(f"{key} → {DEST_BUCKET}/{dest_key}")

    store.save_processed_files(processed)
    get_dagid_by_tag(result,context=context)

with DAG(
    dag_id="input_bucket_csv",
    start_date=days_ago(1),
    catchup=False,
    schedule_interval=None,
    tags=["input"],
) as dag:   
    wait_for_new_file = catch_input_bucket(
        task_id="wait_for_new_csv",
        poke_interval=10,
        timeout=60,
        mode="poke",
    )
    transfer_task = PythonOperator(
        task_id="transfer_new_csv_to_airflow_data",
        python_callable=transfer_file,
        provide_context=True,
    )

wait_for_new_file >> transfer_task 