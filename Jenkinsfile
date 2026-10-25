pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_NAME = "phishguard:${BUILD_NUMBER}"
        CONTAINER_NAME = "phishguard-ci-${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install and test') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv .jenkins-venv
                    .jenkins-venv/bin/python -m pip install --upgrade pip
                    .jenkins-venv/bin/python -m pip install -e ".[dev]"
                    .jenkins-venv/bin/python -m pytest -q
                '''
            }
        }

        stage('Build Docker image') {
            steps {
                sh 'docker build --tag "$IMAGE_NAME" .'
            }
        }

        stage('Container smoke test') {
            steps {
                sh '''
                    set -eu
                    docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true
                    docker run --detach --name "$CONTAINER_NAME" --publish 18000:8000 "$IMAGE_NAME"

                    cleanup() {
                        docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true
                    }
                    trap cleanup EXIT

                    ready=0
                    for attempt in $(seq 1 30); do
                        if curl --fail --silent http://127.0.0.1:18000/health >/tmp/phishguard-health.json; then
                            ready=1
                            break
                        fi
                        sleep 2
                    done
                    test "$ready" -eq 1
                    grep -q '"status":"ok"' /tmp/phishguard-health.json
                    curl --fail --silent --request POST http://127.0.0.1:18000/predict \
                        --header 'Content-Type: application/json' \
                        --data '{"url":"https://www.google.com"}' | grep -q '"prediction"'
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true
                docker rmi "$IMAGE_NAME" >/dev/null 2>&1 || true
                rm -rf .jenkins-venv
            '''
        }
    }
}
