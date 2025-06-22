#!/bin/bash

set -e

# DB 초기화 (최초 1회만 실행됨)
airflow db init

# 관리자 계정 생성 (존재하지 않으면)
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin

# Airflow 웹서버 실행
# exec airflow webserver

