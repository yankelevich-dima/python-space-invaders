node {

    try {

        stage 'Checkout'
            checkout scm

        stage 'Test'

            sh """#!/bin/bash
                export PATH="/root/miniconda3/bin:$PATH"
                conda remove -y --name venv_${env.BRANCH_NAME} --all
                conda create -y --name venv_${env.BRANCH_NAME}
                source activate venv_${env.BRANCH_NAME}

                pip install flake8
                flake8 ./
            """

            sh"""#!/bin/bash
                export PATH="/root/miniconda3/bin:$PATH"
                source activate venv_${env.BRANCH_NAME}

                pip install -r websocket_server/requirements.txt
                cd websocket_server && python tests.py
            """

        if (env.BRANCH_NAME == 'master') {
            stage 'Deploy'
                sh 'cd deploy && echo "193.124.177.175 ansible_ssh_user=deploy" > ./inventory.ini'
                sh "cd deploy && ansible-playbook --private-key ~/.ssh/id_rsa -i inventory.ini playbook-deploy.yml --extra-vars \"BRANCH_NAME=${env.BRANCH_NAME} WEBSOCKET_PORT=9000\""
        } else if (env.BRANCH_NAME == 'develop') {
            stage 'Deploy'
                sh 'cd deploy && echo "193.124.177.175 ansible_ssh_user=deploy" > ./inventory.ini'
                sh "cd deploy && ansible-playbook --private-key ~/.ssh/id_rsa -i inventory.ini playbook-deploy.yml --extra-vars \"BRANCH_NAME=${env.BRANCH_NAME} WEBSOCKET_PORT=9001\""
        }

    } catch (err) {
        throw err
    }

}
