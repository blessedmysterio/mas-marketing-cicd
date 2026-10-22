// CI/CD pipeline for the MAS marketing simulation.
// CI : lint -> unit tests (JUnit + coverage) -> Docker build -> container smoke test
// CD : push to Docker Hub -> deploy simulation Job to Kubernetes (Minikube)
pipeline {
    agent any

    parameters {
        string(name: 'DOCKERHUB_USER', defaultValue: 'blessedmysterio', description: 'Docker Hub namespace')
        booleanParam(name: 'PUSH_IMAGE', defaultValue: true, description: 'Push the image to Docker Hub')
        booleanParam(name: 'DEPLOY_K8S', defaultValue: true, description: 'Deploy the simulation Job to Minikube')
        string(name: 'SIM_RUNS', defaultValue: '30', description: 'Paired runs per scenario in the K8s Job')
    }

    triggers {
        githubPush()                 // webhook from GitHub (needs a public Jenkins URL / ngrok)
        pollSCM('H/2 * * * *')       // fallback for a local Jenkins: check for new commits every 2 min
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_NAME = "${params.DOCKERHUB_USER}/mas-marketing"
        VENV       = "${WORKSPACE}/.venv"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
                }
                echo "Building ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    python3 -m venv "$VENV"
                    . "$VENV/bin/activate"
                    pip install --quiet --upgrade pip
                    pip install --quiet -r requirements-dev.txt
                    pip install --quiet -e .
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '. "$VENV/bin/activate" && flake8 src tests'
            }
        }

        stage('Unit tests') {
            steps {
                sh '''
                    . "$VENV/bin/activate"
                    mkdir -p reports
                    pytest --junitxml=reports/junit.xml \
                           --cov=mas_marketing --cov-report=term --cov-report=xml:reports/coverage.xml
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                    archiveArtifacts artifacts: 'reports/*.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Build Docker image') {
            steps {
                sh '''
                    docker build --target test -t "$IMAGE_NAME:test-$IMAGE_TAG" .
                    docker build --target runtime \
                        --label org.opencontainers.image.revision="$GIT_SHORT" \
                        -t "$IMAGE_NAME:$IMAGE_TAG" -t "$IMAGE_NAME:latest" .
                    docker image ls "$IMAGE_NAME"
                '''
            }
        }

        stage('Smoke test container') {
            steps {
                sh '''
                    rm -rf results && mkdir -p results && chmod 777 results
                    docker run --rm -v "$WORKSPACE/results:/app/results" "$IMAGE_NAME:$IMAGE_TAG" \
                        --scenario S2 --runs 5 --agents 200 --steps 20 --out /app/results
                    test -s results/summary.json
                    cat results/summary.json
                '''
            }
            post {
                success { archiveArtifacts artifacts: 'results/**', fingerprint: true }
            }
        }

        stage('Push to Docker Hub') {
            when {
                allOf {
                    expression { params.PUSH_IMAGE }
                    anyOf { branch 'main'; expression { env.BRANCH_NAME == null } }
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
                    sh '''
                        echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
                        docker push "$IMAGE_NAME:$IMAGE_TAG"
                        docker push "$IMAGE_NAME:latest"
                    '''
                }
            }
            post { always { sh 'docker logout || true' } }
        }

        stage('Deploy to Minikube') {
            when { expression { params.DEPLOY_K8S && params.PUSH_IMAGE } }
            steps {
                sh '''
                    kubectl config use-context minikube
                    kubectl apply -f k8s/namespace.yaml -f k8s/pvc.yaml
                    kubectl -n mas-research delete job mas-simulation --ignore-not-found
                    sed -e "s|IMAGE_PLACEHOLDER|$IMAGE_NAME:$IMAGE_TAG|" \
                        -e "s|RUNS_PLACEHOLDER|$SIM_RUNS|" k8s/job.yaml | kubectl apply -f -
                    kubectl -n mas-research wait --for=condition=complete job/mas-simulation --timeout=300s
                    kubectl -n mas-research logs job/mas-simulation
                '''
            }
        }
    }

    post {
        success { echo "Pipeline OK: ${IMAGE_NAME}:${IMAGE_TAG}" }
        failure { echo 'Pipeline FAILED - see the stage log above' }
        always {
            sh 'docker image prune -f || true'
            cleanWs(deleteDirs: true, notFailBuild: true, patterns: [[pattern: '.venv/**', type: 'INCLUDE']])
        }
    }
}
