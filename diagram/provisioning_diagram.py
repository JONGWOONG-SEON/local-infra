from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Nginx
from diagrams.custom import Custom
from diagrams.onprem.iac import Terraform, Ansible
from diagrams.onprem.container import Docker
from diagrams.onprem.workflow import Airflow
from diagrams.k8s.compute import STS as StatefulSet, Pod
from diagrams.k8s.infra import Node
from diagrams.onprem.gitops import ArgoCD

grap_config = {
    "fontname": "Sans-Serif",
    "fontsize": "36",
    "size": "13.33,7.50!",
    "dpi": "150",
    "ratio": "0.5625",
    "pad" : "0.0",
    "nodesep": "0.0",
    "ranksep": "0.0"
}
node_config={
    "fontsize": "30",
    "fontname": "Sans-Serif",
    "width" : "2.0",
    "height" : "2.0",
    "fixedsize": "true",
    "imagescale": "true",
    "imagepos": "tc",
    "margin": "0.0"
}

module_config = {
    "imagescale":"true",
    "width":"2.0",
    "height":"2.4",
    "fixedsize":"true",
    "margin": "10.0"
}

with Diagram("On-Premises Provisinor"
             ,graph_attr=grap_config
             , node_attr=node_config
             , outformat="jpg"
             , show= False):
    with Cluster("Host Space", graph_attr=grap_config):
        terraform = Terraform("IaC",**module_config)
        kind = Custom('Container Orchestration', "./img/kind.png")
        ansible = Ansible("Configuration Management",**module_config)

        with Cluster("Node Container",graph_attr=grap_config):
            docker_container = [
                Docker("worker1"),
                Docker("worker2"),
                Docker("worker3"),
                Docker("worker4")]

    with Cluster("K8S Space",graph_attr=grap_config):

        with Cluster("Worker1 : Nginx, Minio",graph_attr=grap_config):
            dummy = Node(
            "", 
            width="4", 
            height="0.0", 
            fixedsize="true", 
            style="invis"
            )
            module1 = [Nginx("Ingress",**module_config),
                        Custom('Object Storage', "./img/minio.png")]
            # pod1 = StatefulSet("",**module_config)
            host1 = Node("worker1",**module_config)

        with Cluster("Worker2 : Airflow",graph_attr=grap_config):
            dummy = Node(
            "", 
            width="4", 
            height="0.0", 
            fixedsize="true", 
            style="invis"
            )
            module2 = [Airflow("WebServer",**module_config)
                        ,Airflow("Scheduler",**module_config)
                        ,Airflow("GitSync",**module_config)]
            # pod2 = StatefulSet("",**module_config)
            host2 = Node("worker2",**module_config)

        with Cluster("Worker3 : Posgtres, Gitea",graph_attr=grap_config):
            dummy = Node(
            "", 
            width="4", 
            height="0.0", 
            fixedsize="true", 
            style="invis"
            )
            module3 = [PostgreSQL("Meta And Mart",**module_config)
                        , Custom("Gitea", "./img/gitea.png")
                        , Custom("GiteaAction", "./img/gitea.png")
                        , Pod("WebHook", **module_config)]
            # pod3 = StatefulSet("",**module_config)
            host3 = Node("worker3",**module_config)

        with Cluster("Worker4 : ArgoCD, Streamlit",graph_attr=grap_config):
            dummy = Node(
            "", 
            width="4", 
            height="0.0", 
            fixedsize="true", 
            style="invis"
            )
            module4 = [ArgoCD("Continuous Deployment",**module_config),
                       Custom("BI as Code", "./img/streamlit.png")]
            # pod4 = StatefulSet("",**module_config)
            host4 = Node("worker4",**module_config)
        
            ansible >> Edge(color="brown") >> host4 >> module4
            ansible >> Edge(color="brown") >> host3 >> module3
            ansible >> Edge(color="brown") >> host2 >> module2
            ansible >> Edge(color="brown") >> host1 >> module1

    terraform >> kind >> docker_container << ansible 
    
