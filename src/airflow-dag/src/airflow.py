from airflow.exceptions import AirflowSkipException
import polars as pl
from io import StringIO

def result_xcom_pull(**kwargs):
    """
    tag = input 인 Dag 에서 Xcom으로 처리된 결과 리스트를 확인하는 함수
    """
    data = kwargs["dag_run"].conf.get("input_result")
    if not data:
        raise AirflowSkipException("DAG A에서 데이터를 가져올 수 없어 중단")
    
    return data

def list_csv_keys(bucket:str,prefix:str,paginator,pull_task,**kwargs) -> list[dict]:
    """"
    Xcom 에서 반환한 결과 값을 S3 에서 조회하여 인자를 추출하는 함수
    """
    
    ti = kwargs['ti']
    input_result = ti.xcom_pull(task_ids=pull_task)

    rows: list[list[str]] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key not in input_result:
                continue

            print(f"keys:{key} \n insert_result:{input_result}")
            basename = key.rsplit("/", 1)[-1]      
            name, _ext = basename.rsplit(".", 1)   
            parts = name.split("_")                
            
            if len(parts) != 4:
                continue

            table     = parts[0] if len(parts) > 0 else ""
            version   = parts[1] if len(parts) > 1 else ""
            describe  = parts[2] if len(parts) > 2 else ""
            timestamp = parts[3] if len(parts) > 3 else ""

            rows.append([key, table, version, describe, timestamp])
    return rows

def read_csv_from_s3(bucket:str, key:list, s3, **kwargs) -> pl.DataFrame:
    """
    인자, key를 기반으로 데이터를 읽어오는 함수
    """

    obj = s3.get_object(Bucket=bucket, Key=key[0])
    
    data = obj["Body"].read().decode("utf-8",errors="ignore")

    df = pl.read_csv(
        StringIO(data),
        infer_schema_length=None,
        low_memory=False
    )
    return df
