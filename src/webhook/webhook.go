package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
)

type MinioEvent struct {
	Records []struct {
		EventName string `json:"eventName"`
		S3        struct {
			Bucket struct {
				Name string `json:"name"`
			} `json:"bucket"`
			Object struct {
				Key string `json:"key"`
			} `json:"object"`
		} `json:"s3"`
	} `json:"Records"`
}

type EnvStruct struct {
	airflow_host     string
	airflow_port     string
	airflow_username string
	airflow_password string
	airflow_db_path  string
}

func loadEnv() *EnvStruct {
	_ = godotenv.Load()
	airflow_host := os.Getenv("AIRFLOW_HOST")
	airflow_port := os.Getenv("AIRFLOW_PORT")
	airflow_username := os.Getenv("AIRFLOW_USERNAME")
	airflow_password := os.Getenv("AIRFLOW_PASSWORD")
	airflow_db_path := os.Getenv("AIRFLOW_DB_PATH")
	return &EnvStruct{
		airflow_host,
		airflow_port,
		airflow_username,
		airflow_password,
		airflow_db_path,
	}
}

func get_dagid(env *EnvStruct, bucket string, tag string) error {
	var rows *sql.Rows
	var err error

	db, err := sql.Open("postgres", env.airflow_db_path)
	if err != nil {
		log.Fatal("DB Connect Failed: %v", err)
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		log.Fatalf("DB Network Failed: %v", err)
	}
	fmt.Printf("DB Connect\n")

	if bucket == "input" {
		script := `SELECT b.name ,b.dag_id 
					FROM dag a 
					LEFT JOIN dag_tag b
					ON a.dag_id = b.dag_id
					WHERE a.is_active = TRUE AND b.name = $1`
		rows, err = db.Query(script, bucket)
	} else {
		script := `SELECT b.name ,b.dag_id 
					FROM dag a 
					LEFT JOIN dag_tag b
					ON a.dag_id = b.dag_id
					WHERE a.is_active = TRUE AND b.name = $1`
		rows, err = db.Query(script, tag)
	}

	if err != nil {
		return fmt.Errorf("Query Extract Failed: %v", err)
	}

	for rows.Next() {
		var name string
		var dag_id string

		if err := rows.Scan(&name, &dag_id); err != nil {
			log.Fatal("Query Extract Failed:", err)
		} else {
			return triggerAirflowDAG(env, dag_id)
		}
	}
	return nil
}

func triggerAirflowDAG(env *EnvStruct, dagid string) error {

	if env.airflow_host == "" || env.airflow_port == "" || env.airflow_username == "" || env.airflow_password == "" {
		return fmt.Errorf("Invaild Env. (AIRFLOW_HOST, AIRFLOW_PORT, AIRFLOW_USERNAME, AIRFLOW_PASSWORD)")
	}

	url := fmt.Sprintf("%s:%s/api/v1/dags/%s/dagRuns", env.airflow_host, env.airflow_port, dagid)

	payload := map[string]interface{}{
		"conf": map[string]interface{}{
			"source": "minio-webhook",
		},
	}
	jsonData, _ := json.Marshal(payload)

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.SetBasicAuth(env.airflow_username, env.airflow_password)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("DAG Trigger Failed [%d]: %s", resp.StatusCode, body)
	}

	fmt.Sprintf("%s DAG Trigger Success", dagid)

	return nil
}

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	var event MinioEvent
	env := loadEnv()
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Content Read Error", http.StatusBadRequest)
		return
	}

	err = json.Unmarshal(body, &event)
	if err != nil {
		http.Error(w, "JSON Parsing Error", http.StatusBadRequest)
		return
	}

	for _, record := range event.Records {
		tag_full := strings.Split(record.S3.Object.Key, "%2F")
		tag := tag_full[0]
		log.Printf("POST Event: Bucket[%s], Files[%s]\n",
			record.S3.Bucket.Name, record.S3.Object.Key)

		if err := get_dagid(env, record.S3.Bucket.Name, tag); err != nil {
			log.Printf("DAG Trigger Failed On Http Request: %v\n", err)
		}
	}

	w.WriteHeader(http.StatusOK)
	w.Write([]byte("ok"))
}

func main() {
	http.HandleFunc("/minio/webhook", webhookHandler)
	log.Println("Webhook Server Start")
	http.ListenAndServe(":8081", nil)
}
