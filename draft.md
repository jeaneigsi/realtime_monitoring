
  # minio-init:
  #   image: minio/mc
  #   container_name: minio-init
  #   depends_on:
  #     - minio
  #   environment:
  #     - MINIO_ENDPOINT=http://minio:9000
  #     - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-admin}
  #     - MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-admin123}
  #   entrypoint: sh
  #   command: /app/initialize.sh
  #   volumes:
  #     - ./minio:/app
  #   networks:
  #     - reseau_raffinerie

  # flink-jobmanager:
  #   image: ./flink
  #   container_name: flink-jobmanager
  #   hostname: flink-jobmanager
  #   ports:
  #     - "8081:8081"
  #   command: jobmanager
  #   environment:
  #     - JOB_MANAGER_RPC_ADDRESS=flink-jobmanager
  #     - |
  #       FLINK_PROPERTIES=
  #       jobmanager.rpc.address: flink-jobmanager
  #   networks:
  #     reseau_raffinerie:
  #       aliases:
  #         - flink-jobmanager

  # flink-taskmanager:
  #   image: ./flink
  #   container_name: flink-taskmanager
  #   depends_on:
  #     - flink-jobmanager
  #   command: taskmanager
  #   environment:
  #     - JOB_MANAGER_RPC_ADDRESS=flink-jobmanager
  #     - TASK_MANAGER_NUMBER_OF_TASK_SLOTS=2
  #     - |
  #       FLINK_PROPERTIES=
  #       jobmanager.rpc.address: flink-jobmanager
  #       taskmanager.numberOfTaskSlots: 2
  #   networks:
  #     - reseau_raffinerie

  # flink-job:
  #   build:
  #     context: ./flink
  #   container_name: flink-job
  #   command: ["/bin/bash", "-c", "/opt/flink/check_kafka.sh && /opt/flink/monitor_flink_job.sh"]
  #   restart: on-failure
  #   environment:
  #     - PYFLINK_PYTHON=/usr/bin/python3
  #     - POSTGRES_USER=${POSTGRES_USER:-tsdbadmin}
  #     - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}
  #     - DB_HOST=timescaledb
  #     - DB_PORT=5432
  #     - DB_NAME=${POSTGRES_DB:-postgres}
  #     - MINIO_ENDPOINT=minio:9000
  #     - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-admin}
  #     - MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-admin123}
  #     - PYTHONUNBUFFERED=1
  #     - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
  #     - KAFKA_TOPIC=raw_data
  #     - KAFKA_RETRY_MAX_ATTEMPTS=10
  #     - JAVA_OPTS="-Djava.net.preferIPv4Stack=true"
  #   depends_on:
  #     - flink-jobmanager
  #     - flink-taskmanager
  #     - kafka
  #     - timescaledb
  #     - minio
  #   healthcheck:
  #     test: ["CMD-SHELL", "nc -z kafka 9092 || exit 1"]
  #     interval: 30s
  #     timeout: 10s
  #     retries: 3
  #     start_period: 60s
  #   networks:
  #     - reseau_raffinerie

  # # spark-master:
  # #   image: bitnami/spark:3.3
  # #   container_name: spark-master
  # #   environment:
  # #     - SPARK_MODE=master
  # #   ports:
  # #     - "7077:7077"
  # #     - "8082:8080"
  # #   networks:
  # #     - reseau_raffinerie

  # # spark-worker:
  # #   image: bitnami/spark:3.3
  # #   container_name: spark-worker
  # #   environment:
  # #     - SPARK_MODE=worker
  # #     - SPARK_MASTER_URL=spark://spark-master:7077
  # #     - SPARK_WORKER_MEMORY=1g
  # #     - SPARK_WORKER_CORES=1
  # #   depends_on:
  # #     - spark-master
  # #   networks:
  # #     - reseau_raffinerie

  # # spark-job:
  # #   build:
  # #     context: ./Spark
  # #   container_name: spark-job
  # #   hostname: spark-job
  # #   environment:
  # #     - POSTGRES_USER=${POSTGRES_USER:-tsdbadmin}
  # #     - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}
  # #     - DB_HOST=timescaledb
  # #     - DB_PORT=5432
  # #     - DB_NAME=${POSTGRES_DB:-postgres}
  # #     - MINIO_ENDPOINT=http://minio:9000
  # #     - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-admin}
  # #     - MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-admin123}
  # #     - PYTHONUNBUFFERED=1
  # #     - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
  # #     - KAFKA_TOPIC=raw_data
  # #   volumes:
  # #     - ./Spark:/opt/spark/jobs
  # #     - /tmp/spark_checkpoints:/tmp/spark_checkpoints
  # #   command: >
  # #     spark-submit 
  # #     --master spark://spark-master:7077 
  # #     --deploy-mode client 
  # #     --conf spark.jars.ivy=/tmp/.ivy 
  # #     --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2,org.postgresql:postgresql:42.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk:1.12.262
  # #     --conf "spark.driver.extraJavaOptions=-Djava.net.preferIPv4Stack=true"
  # #     --conf "spark.executor.extraJavaOptions=-Djava.net.preferIPv4Stack=true"
  # #     --conf "spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem"
  # #     --conf "spark.hadoop.fs.s3a.endpoint=http://minio:9000"
  # #     --conf "spark.hadoop.fs.s3a.path.style.access=true"
  # #     --conf "spark.hadoop.fs.s3a.access.key=admin"
  # #     --conf "spark.hadoop.fs.s3a.secret.key=admin123"
  # #     /opt/spark/jobs/kafka_spark.py
  # #   restart: on-failure
  # #   depends_on:
  # #     - kafka
  # #     - spark-master
  # #     - timescaledb
  # #     - minio
  # #   networks:
  # #     - reseau_raffinerie
