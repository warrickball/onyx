#### Start gunicorn
```
$ gunicorn metadb.wsgi -c gunicorn.conf.py
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
celery -A metadb beat -l INFO
celery -A metadb worker -Q create_mpx_tables --concurrency=1 -l INFO
```
