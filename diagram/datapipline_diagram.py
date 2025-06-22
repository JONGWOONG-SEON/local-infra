from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Nginx
from diagrams.custom import Custom
from diagrams.onprem.workflow import Airflow
from diagrams.k8s.network import SVC
from diagrams.k8s.compute import Pod
from diagrams.k8s.infra import Node
from diagrams.onprem.gitops import ArgoCD
from diagrams.onprem.client import User
from diagrams.programming.language import Go
from diagrams.c4 import Person, Container, Database, System, SystemBoundary, Relationship
from textwrap import dedent

graph_config = {
    # "fontname": "Sans-Serif",
    # "fontsize": "36",
    "size":"13.33,7.50!",
    "ratio": "0.5",
    "pad" : "0.0",
    "nodesep": "0.0",
    "ranksep": "1.2",
    "dpi": "300",
    "splines": "spline"
}
node_config={
    "fontsize": "14",
    "fontname": "Sans-Serif",
    # "width" : "2.0",
    # "height" : "2.0",
    "fixedsize": "true",
    "imagescale": "true",
    "imagepos": "tc",
    "margin": "10.0"
}
module_config = {
    "imagescale":"true",
    "width":"2.2",
    "height":"2.4",
    "fixedsize":"true",
    "margin": "10.0"
}
graph_attributes = {
    "fontsize": "14", 
    "bgcolor": "white",
    "margin": "10",
    "style": "dashed",
}

with Diagram("DataPipline", 
             direction="LR", 
             graph_attr=graph_config,
             outformat='jpg', 
            #  node_attr=node_config, 
             show=False):
    ClientToMinio = Relationship(label="Rules: {table}_{version}_{describe}.csv")
    Client = Person(
        name = "Client",
        description = 
    "mc tool을 활용\n"
    "Input Bucket에 데이터 삽입 "
    )
    # Bridge = 
    with SystemBoundary("Input Proccess"):
        Minio = Custom("Object Storage", "./img/minio.png")
        MinioToWebhook = Relationship(label="Mc Event Trigger")    
        Webook = Container(
                    name= "Webhook Application",
                    technology= "Golang",
                    description= "새로운 데이터 감지DagTrigger"
                )
        with SystemBoundary("ETL Proccess"):
            InputDag = Container(
                name = "Dag:input_bucket_csv",
                technology = "Airflow",
                description = "result/{table}/로 이관 후행 Dag 실행"
            )
            DBDag = Container(
                name = "Dag:superstore_insert_pg",
                technology = "Dag",
                description = "Table 생성 및 Property 관리, 데이터 Insert"
            )
            with SystemBoundary("Input Task"):
                InputTask1 = Container(
                    name = "Task:wait for new csv",
                    technology = "BaseSensorOperator",
                    description = "신규 파일을 감지하여 result/{table} 로 이관"
                )
                InputTask2 = Container(
                    name = "Task:transfer_new_csv_to_airflow_data",
                    technology = "PythonOperator",
                    description = "xcom 에 처리 파일을 작성 후행 Dag 실행"
                )
            with SystemBoundary("DB Task"):
                DBTask1 = Container(
                    name = "Task:xcom_pull",
                    technology = "xcom",
                    description = "Input Dag Result Xcom 을 확인, 유효체크"
                )
                DBTask2 = Container(
                    name = "Task:superstore_task_id",
                    technology = "Polars,sqlalchemy",
                    description = "처리 파일 기준으로 Bucket 에서 불러와 Postgres 에 적재"
                )
        with SystemBoundary(""):
            table = Database(name="Database",
                technology="Postgres",
                description="estore 스키마에 {table} 기준으로 적재")
            streamlit = System(name="BI as Code",
                        description="검증용 BI 웹프레임워크",
                        external=True)
    with Cluster("Input System"):
        MinioPod = Custom("Object Sotrage", "./img/minio.png")
        WebookPod = Pod("Webhook Pod")
        MinioSVC = SVC("Minio NodeIP")
        
        
        with Cluster("Services"):
            PostgresSVC = SVC("Postgres Services")
            AirflowSVC = SVC("Airflow Service")
            NginxController = Nginx("Ingress Controller")
        
        with Cluster("Pods"):
            PostgresPods = PostgreSQL("Postgres Pods")
            AirflowPods = Airflow("Airflow Pods")
            



    # Webook >> Relationship(style="invis") >> [AirflowSVC,PostgresSVC]
    # 논리
    Client >> ClientToMinio >> Minio >> MinioToWebhook >> Webook >> Relationship("API Request")  >> InputDag
    InputDag >> Relationship(style="invis") >> [InputTask1,InputTask2] >> Relationship(style="invis") >> DBDag >> Relationship(style="invis") >> [DBTask1,DBTask2]
    InputDag >> Relationship() >> InputTask1
    InputTask2 >> Relationship() >> DBDag
    DBDag >> Relationship () >> DBTask1
    DBTask2 >> Relationship() >> table >> Relationship() >> streamlit

    # 물리
    Client >> MinioSVC >> WebookPod >> NginxController >> [AirflowSVC,PostgresSVC]
    PostgresSVC >> PostgresPods
    AirflowSVC >> AirflowPods >> AirflowSVC
