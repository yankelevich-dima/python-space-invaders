# Деплой проекта

### 1. Подготовка сервера

Установка docker для контейнеризации.

 - Необходимо создать файл `inventory.ini`, создержащий данные для входа на сервер.
 - ansible-playbook playbook-preparing.yml -i `<inventory.ini>`  --private-key `<private_key>`

### 2. Установка Jenkins

Сборка контейнера с Jenkins для автодеплоя.

 - Создать аналогичный файл для пользователя **deploy**
 - ansible-playbook playbook-jenkins.yml -i `<inventory.ini>`  --private-key `<private_key>`

### 3. Автодеплой серверной части

 - В контейнере Jenkins сгенерить пару ssh-ключей, открытый закинуть в репозиторий проекта, а также в `authorized_keys` пользователю **deploy** на сервере.
 - Указать путь к ключу в Jenkinsfile (по умолчанию ~/.ssh/id_rsa), а также ip сервера.
 - Сконфигурировать Jenkins multibranch pipeline, добавить туда git проекта.
