pipeline {
    agent any

    triggers {
        githubPush()
    }

    parameters {
        choice(name: 'JOB_TYPE', choices: ['pi_estimation', 'word_count'], description: 'Spark job to run on Cloudera')
        string(name: 'NUM_EXECUTORS',   defaultValue: '2',    description: 'Number of YARN executors')
        string(name: 'EXECUTOR_MEMORY', defaultValue: '512m', description: 'Memory per executor')
    }

    environment {
        CLOUDERA_HOST = 'ec2-user@13.41.167.97'
        SSH_KEY       = '/var/lib/jenkins/.ssh/id_rsa'
        SPARK_SCRIPTS = '/opt/spark-jobs'
    }

    stages {

        stage('Checkout from GitHub') {
            steps {
                checkout scm
            }
        }

        stage('Copy Script to Cloudera') {
            steps {
                sh '''
                    echo "=== Copying transformation.py to /tmp on Cloudera master ==="
                    scp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
                        src/transformation.py \
                        ${CLOUDERA_HOST}:/tmp/transformation.py
                '''
            }
        }

        stage('Submit Spark Job') {
            steps {
                sh '''
                    echo "=== Submitting ${JOB_TYPE} to YARN on Cloudera master ==="
                    ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${CLOUDERA_HOST} "
                        export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
                        export HADOOP_CONF_DIR=/etc/hadoop/conf
                        export SPARK_CONF_DIR=/etc/spark/conf
                        export PYSPARK_PYTHON=/usr/bin/python3
                        spark-submit \
                          --master yarn \
                          --deploy-mode client \
                          --name ${JOB_TYPE}-jenkins-build-${BUILD_NUMBER} \
                          --num-executors ${NUM_EXECUTORS} \
                          --executor-cores 1 \
                          --executor-memory ${EXECUTOR_MEMORY} \
                          --driver-memory 512m \
                          --conf spark.pyspark.python=/usr/bin/python3 \
                          /tmp/transformation.py
                    "
                '''
            }
        }

        
    }

    post {
        success { echo 'Spark job completed successfully on Cloudera YARN.' }
        failure { echo 'Spark job failed. Check SSH/YARN logs above.' }
    }
}
    