node {

    try {

        stage 'Checkout'
            checkout scm

        stage 'Test'
            sh 'virtualenv -p python3 venv'
            sh 'flake8 --exclude=venv ./'

            # Server tests
            sh '''#!/bin/bash
                source ./venv/bin/activate
                pip install -r server/requirements.txt
                coverage run --omit '*venv*' server/tests.py
            '''
            sh '''#!/bin/bash
                percentage=$(coverage report --omit server/tests.py | grep TOTAL | rev | cut -c -3 | rev | cut -c -2)
                if [ $percentage -lt 60 ]; then echo "Low coverage!"; exit 1; fi
            '''
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
