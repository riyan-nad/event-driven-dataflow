pipeline {
    agent any

    environment {
        TF_IN_AUTOMATION = "true"
    }

    stages {
        stage('Checkout') {
            steps {
                git credentialsId: 'github', url: 'https://github.com/riyan-nad/event-driven-dataflow.git'
            }
        }

        stage('Terraform Init') {
            steps {
                sh 'terraform init'
            }
        }

        stage('Terraform Plan') {
            steps {
                sh 'terraform plan'
            }
        }

        stage('Terraform Apply') {
            steps {
                sh 'terraform apply -auto-approve'
            }
        }
    }
}
