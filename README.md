# `onyx`

#### Start gunicorn
```
$ gunicorn onyx.wsgi -c gunicorn.conf.py
```

#### Stop gunicorn
```
$ pkill gunicorn
```

#### Run tests
```
$ python manage.py test -v 2
$ python manage.py test data.tests -v 2
$ python manage.py test accounts.tests -v 2
```

#### Run celery 
```
celery -A onyx beat -l INFO
celery -A onyx worker -Q create_mpx_tables --concurrency=1 -l INFO
```
