#!/usr/bin/env bash
cd "${0%/*}"
cd ..

if [ -d $1 ]
then
    PROJECT_DIR=`(cd ${1}; pwd)`
    PROJECT=`basename $PROJECT_DIR`

    echo "Activating Python virtual environment..."
    source .venv/bin/activate

    cd onyx/

    echo "Symlinking ${PROJECT} models..."
    ln -s ${PROJECT_DIR}/models.py data/models/projects/${PROJECT}.py

    echo "Symlinking ${PROJECT} serializers..."
    ln -s ${PROJECT_DIR}/serializers.py data/serializers/projects/${PROJECT}.py

    echo "Making ${PROJECT} database migrations..."
    python manage.py makemigrations data accounts internal
    python manage.py migrate

    echo "Creating ${PROJECT} project..."
    python manage.py project ${PROJECT_DIR}/project.json

    echo "Creating ${PROJECT} choices..."
    python manage.py choices ${PROJECT_DIR}/choices.json

    echo "Creating ${PROJECT} choice constraints..."
    python manage.py choiceconstraints ${PROJECT_DIR}/constraints.json

    echo "Validating ${PROJECT} choice constraints..."
    python manage.py choiceconstraints --validate

    if [ ! -z $2 ] 
    then
        echo "Granting '${2}' user the roles and permissions required for ${PROJECT}..."
        python manage.py user groups $2 --grant ${PROJECT}.add.base ${PROJECT}.view.base ${PROJECT}.change.base ${PROJECT}.delete.base ${PROJECT}.add.admin ${PROJECT}.view.admin ${PROJECT}.change.admin
    fi
else
    echo "Invalid project directory: ${1}"
fi
