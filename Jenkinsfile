node {

    try {

        stage 'Checkout'
            checkout scm

        stage 'Test'
            sh 'virtualenv -p python3.5 venv'

            sh '''#!/bin/bash
                source ./venv/bin/activate
                pip install flake8
                flake8 --exclude=venv ./
            '''

            sh '''#!/bin/bash
                source ./venv/bin/activate
                pip install -r websocket_server/requirements.txt
                coverage run --omit '*venv*' --source './' websocket_server/tests.py
            '''
            sh '''#!/bin/bash
                source ./venv/bin/activate
                coverage report --omit websocket_server/tests.py
            '''

            sh 'rm -rf venv'

        if (env.BRANCH_NAME == 'master') {
            stage 'Deploy'
                sh 'cd deploy && echo "193.124.177.175 ansible_ssh_user=deploy" > ./inventory.ini'
                sh "cd deploy && ansible-playbook --private-key ~/.ssh/id_rsa -i inventory.ini playbook-deploy.yml --extra-vars \"BRANCH_NAME=${env.BRANCH_NAME} FLASK_PORT=8001 WEBSOCKET_PORT=9001\""
        } else if (env.BRANCH_NAME == 'develop') {
            stage 'Deploy'
                sh 'cd deploy && echo "193.124.177.175 ansible_ssh_user=deploy" > ./inventory.ini'
                sh "cd deploy && ansible-playbook --private-key ~/.ssh/id_rsa -i inventory.ini playbook-deploy.yml --extra-vars \"BRANCH_NAME=${env.BRANCH_NAME} PORT=8002 WEBSOCKET_PORT=9002\""
        }

    } catch (err) {
        throw err
    }

}
