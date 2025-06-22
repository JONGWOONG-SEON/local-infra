from airflow import DAG
from airflow.models import DagModel
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.utils.state import State
from datetime import datetime
from airflow.settings import Session
from airflow.operators.python import get_current_context
from zoneinfo import ZoneInfo

def get_dagid_by_tag(result : dict,**context):
    """
    minio result 버킷에서 table명과 tag명은 동일함을 원칙으로 함
    즉, Path = Tag = Table 명을 동일하게 가져가야 정상동작
    """
    _session = Session()
    for key, result_file in result.items():
       _dags = _session.query(DagModel).filter(DagModel.tags.any(name=key))\
                                       .filter(DagModel.is_active == True)\
                                       .filter(DagModel.is_paused == False)\
                                       .all()
       trigger_operator(_dags,result_file,**context)
    _session.close()
    
def trigger_operator(dag,result_file,**context):
    """
    conf 에 input_result 는 후행 Dag에서 처리 할 파일목록으로 고정 값으로 둠
    """
    # traget_dag = get_dagid_by_tag(path)
    now = datetime.utcnow()
    ctx = get_current_context()
    ti  = ctx['ti']
    for dag_model in dag:
        dag_id = dag_model.dag_id
        print(f"DAG 트리거: {dag_id}")
        ti.xcom_push(key="input_result", value = result_file)
        trigger = TriggerDagRunOperator(
                    task_id=f"trigger_{dag_id}",
                    trigger_dag_id=dag_id,
                    conf={
                        "source": "tag_trigger"
                        ,"input_result":result_file}
                    # execution_date=now
                )
        trigger.execute(context=ctx)