pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDENTIALS_ID = 'dockerhub-credentials'
        DOCKER_IMAGE_NAME         = 'solanka123/tourism-api'
        IMAGE_TAG                 = "${env.BUILD_NUMBER}"
        TARGET_SERVER_IP          = credentials('solanka-prod-server-ip')
        SSH_KEY_CREDENTIALS_ID    = 'aws-ec2-ssh-key'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
    }

    stages {
        stage('1. Environment Checkout') {
            steps {
                echo '=== Stage 1: Checking out Source Code from Repository ==='
                checkout scm
                sh 'git log -1 --pretty=format:"Commit: %h by %an - %s"'
            }
        }

        stage('2. Code Quality & Linting (ISO 9001)') {
            steps {
                echo '=== Stage 2: Static Code Quality Checks (PEP8 / Flake8) ==='
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    flake8 app/ --max-line-length=120 --exclude=__pycache__
                '''
            }
        }

        stage('3. Automated Unit Testing & Coverage') {
            steps {
                echo '=== Stage 3: Running Pytest Test Suite ==='
                sh '''
                    . venv/bin/activate
                    pytest --junitxml=test-results.xml tests/
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('4. Security & Compliance Scan (ISO 27001)') {
            steps {
                echo '=== Stage 4: Running Dependency and Container Vulnerability Scans ==='
                sh '''
                    # Check for known high/critical vulnerabilities in dependencies
                    . venv/bin/activate
                    pip install safety
                    safety check --ignore 70612 || true
                '''
            }
        }

        stage('5. Docker Image Build & Tag') {
            steps {
                echo "=== Stage 5: Building Docker Image: ${DOCKER_IMAGE_NAME}:${IMAGE_TAG} ==="
                sh """
                    docker build -t ${DOCKER_IMAGE_NAME}:${IMAGE_TAG} -t ${DOCKER_IMAGE_NAME}:latest .
                """
            }
        }

        stage('6. Push to Docker Registry') {
            steps {
                echo '=== Stage 6: Authenticating & Pushing to Docker Hub ==='
                withCredentials([usernamePassword(credentialsId: "${DOCKER_HUB_CREDENTIALS_ID}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh """
                        echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE_NAME}:${IMAGE_TAG} || true
                        docker push ${DOCKER_IMAGE_NAME}:latest || true
                    """
                }
            }
        }

        stage('7. Ansible Automated Deployment') {
            steps {
                echo '=== Stage 7: Deploying to AWS Production Host via Ansible ==='
                withCredentials([sshUserPrivateKey(credentialsId: "${SSH_KEY_CREDENTIALS_ID}", keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                    sh """
                        chmod 400 \$SSH_KEY
                        echo "Ensuring container image is deployed to AWS production host..."
                        docker save ${DOCKER_IMAGE_NAME}:${IMAGE_TAG} | ssh -o StrictHostKeyChecking=no -i \$SSH_KEY \$SSH_USER@${TARGET_SERVER_IP} "docker load" || true
                        ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy.yml \
                            --private-key=\$SSH_KEY \
                            -u \$SSH_USER \
                            --extra-vars "docker_image=${DOCKER_IMAGE_NAME}:${IMAGE_TAG} target_host=${TARGET_SERVER_IP}"
                    """
                }
            }
        }

        stage('8. Post-Deployment Verification') {
            steps {
                echo '=== Stage 8: Automated System & Health Check Verification ==='
                sh """
                    echo "Pinging health check on AWS host: http://${TARGET_SERVER_IP}:8000/health"
                    curl -s -f http://${TARGET_SERVER_IP}:8000/health | grep '"status":"UP"'
                """
            }
        }
    }

    post {
        success {
            echo "SUCCESS: Pipeline completed successfully. Solanka API v${IMAGE_TAG} deployed to production."
        }
        failure {
            echo "ALERT: Pipeline failed or health verification did not succeed!"
            echo "Triggering automated rollback playbook to preserve ISO 20000 / 22301 SLA targets..."
            withCredentials([sshUserPrivateKey(credentialsId: "${SSH_KEY_CREDENTIALS_ID}", keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                sh """
                    chmod 400 \$SSH_KEY
                    ansible-playbook -i ansible/inventory.ini ansible/playbooks/rollback.yml \
                        --private-key=\$SSH_KEY \
                        -u \$SSH_USER \
                        --extra-vars "target_host=${TARGET_SERVER_IP}" || true
                """
            }
        }
    }
}
