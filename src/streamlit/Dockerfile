FROM registry.local:5000/custom-python:3.12-slim

WORKDIR /app

COPY . .

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=3000", "--server.address=0.0.0.0"]