## Local InfraStruccher 구성

### *installer.sh* 실행
```
Images 및 Local 디펜던시 다운로드
```
### hosts 정보 갱신
```
#local infra
127.0.0.1       minio.local
127.0.0.1       airflow.local
127.0.0.1       argocd.local
127.0.0.1       gitea.local
127.0.0.1       evidence.local
127.0.0.1       streamlit.local
```

### Ansible 설정
```sh
python -m venv venv
pip install -r requirements.txt
```

### Terraform 실행 명령어 
```sh
# Terrafrom 실행환경순
terraform init
terraform plan
terraform apply
```

### minio 버킷 설정
```
vi ~./mc/config.json

추가
                "local": {
                        "url": "http://localhost:30081",
                        "accessKey": "",
                        "secretKey": "",
                        "api": "S3v4",
                        "path": "auto"},

```

### gitea 초기 설정
```
http://gitea.local:30080/ 접근

메타정보 입력
giteaadmin


레포지토리 생성
helm
airflow-dag
streamlit

우측 상단 설정 -> User Settings -> Actions -> Secrets -> Add Secret 발급

디렉토리 ./modules/gitea/vars/runner_configmap.yaml 에서 GITEA_RUNNER_REGISTRATION_TOKEN 추가

```
