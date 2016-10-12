node {

    try {

        stage 'Checkout'
            checkout scm

        stage 'Test'
            sh 'virtualenv venv'
            sh '''#!/bin/bash
                source ./venv/bin/activate
                # run tests here
            '''
            sh 'flake8 --exclude=venv ./'
            sh 'rm -rf venv'

        if (env.BRANCH_NAME == 'master') {
            stage 'Deploy'
                sh 'cd deploy && echo "193.124.177.175 ansible_ssh_user=deploy" > ./inventory.ini'
                sh "cd deploy && ansible-playbook --private-key ~/.ssh/id_rsa -i inventory.ini playbook-deploy.yml --extra-vars \"BRANCH_NAME=${env.BRANCH_NAME} PORT=8001\""
        } else if (env.BRANCH_NAME == 'develop') {
            stage 'Deploy'
                sh 'cd deploy && echo "193.124.177.175 ansible_ssh_user=deploy" > ./inventory.ini'
                sh "cd deploy && ansible-playbook --private-key ~/.ssh/id_rsa -i inventory.ini playbook-deploy.yml --extra-vars \"BRANCH_NAME=${env.BRANCH_NAME} PORT=8002\""
        }

    } catch (err) {
        throw err
    }

}
