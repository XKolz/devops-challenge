FROM jenkins/jenkins:lts

USER root

# Install Docker CLI, AWS CLI, and SSH client
RUN apt-get update && \
    apt-get install -y \
        docker.io \
        awscli \
        openssh-client \
        python3 \
        python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Allow jenkins user to run docker
RUN usermod -aG docker jenkins

USER jenkins
