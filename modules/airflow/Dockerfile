FROM apache/airflow:2.5.1-python3.9
# FROM apache/airflow:slim-3.0.0rc2-python3.9

# 시스템 의존성 설치
USER root

RUN apt-get update && apt-get install -y \
    libpq-dev gcc procps &&\
    apt-get clean

# entrypoint 파일 복사 및 실행 권한 부여
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# airflow 사용자로 전환
USER airflow

# 환경 변수 설정
ENV AIRFLOW_HOME=/opt/airflow
ENV SQLALCHEMY_SILENCE_UBER_WARNING=1

# SQLAlchemy 버전 고정 (2.0 비호환 방지)
RUN pip install --no-cache-dir 'sqlalchemy<2.0'&& \
    pip install --upgrade pip && \
    pip install --no-cache-dir psycopg2-binary --upgrade && \
    pip install --no-cache-dir apache-airflow-providers-postgres && \
    pip install --no-cache-dir apache-airflow[postgres] && \
    pip install --no-cache-dir apache-airflow-providers-google[google_leveldb] &&\
    pip install --no-cache-dir apache-airflow-providers-amazon &&\
    pip install --no-cache-dir polars

ENTRYPOINT ["/entrypoint.sh"]

