# `onyx`

Start the server:
```
$ gunicorn -c onyx/onyx.gunicorn.py
```

Stop the server:
```
$ pkill -f onyx.gunicorn.py
```

View server access/error logs:
```
$ tail -f logs/access.log
$ tail -f logs/error.log
```

Run the tests:
```
$ python manage.py test -v 2
```
