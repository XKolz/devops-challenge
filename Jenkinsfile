pipeline {
    agent any

    environment {
        AWS_REGION     = 'us-east-1'
        ECR_REPOSITORY = 'devops-challenge-prod'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python3 -m pip install --quiet -r app/requirements.txt pytest httpx
                    pytest app/tests/ -v
                '''
            }
        }

        stage('Build') {
            steps {
                script {
                    env.IMAGE_TAG = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
                sh 'docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} ./app'
            }
        }

        stage('Push to ECR') {
            steps {
                withCredentials([
                    string(credentialsId: 'AWS_ACCESS_KEY_ID',     variable: 'AWS_ACCESS_KEY_ID'),
                    string(credentialsId: 'AWS_SECRET_ACCESS_KEY', variable: 'AWS_SECRET_ACCESS_KEY'),
                    string(credentialsId: 'ECR_REGISTRY',          variable: 'ECR_REGISTRY')
                ]) {
                    sh '''
                        export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
                        export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
                        export AWS_DEFAULT_REGION=$AWS_REGION

                        aws ecr get-login-password --region $AWS_REGION \
                          | docker login --username AWS --password-stdin $ECR_REGISTRY

                        docker tag  ${ECR_REPOSITORY}:${IMAGE_TAG} $ECR_REGISTRY/${ECR_REPOSITORY}:${IMAGE_TAG}
                        docker tag  ${ECR_REPOSITORY}:${IMAGE_TAG} $ECR_REGISTRY/${ECR_REPOSITORY}:latest
                        docker push $ECR_REGISTRY/${ECR_REPOSITORY}:${IMAGE_TAG}
                        docker push $ECR_REGISTRY/${ECR_REPOSITORY}:latest
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([
                    string(credentialsId: 'ECR_REGISTRY', variable: 'ECR_REGISTRY'),
                    string(credentialsId: 'EC2_HOST',     variable: 'EC2_HOST'),
                    sshUserPrivateKey(
                        credentialsId: 'EC2_SSH_KEY',
                        keyFileVariable: 'SSH_KEY_FILE'
                    )
                ]) {
                    sh '''
                        ssh -i "$SSH_KEY_FILE" \
                            -o StrictHostKeyChecking=no \
                            ec2-user@"$EC2_HOST" \
                            "
                              aws ecr get-login-password --region $AWS_REGION \
                                | docker login --username AWS --password-stdin $ECR_REGISTRY
                              docker pull $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
                              docker stop app 2>/dev/null || true
                              docker rm   app 2>/dev/null || true
                              docker run -d \
                                --name app \
                                --restart unless-stopped \
                                -p 80:8000 \
                                $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
                              docker image prune -f
                            "
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully — app is live.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }
    }
}
