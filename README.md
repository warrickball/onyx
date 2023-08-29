# `onyx`

API for storing pathogen metadata. 

### Server control
Start the server:
```
$ cd onyx/
$ gunicorn -c onyx.gunicorn.py
```

Stop the server:
```
$ pkill -f onyx.gunicorn.py
```

### Viewing logs
View access logs:
```
$ tail -f logs/access.log
```

View error logs:
```
$ tail -f logs/error.log
```

### Running tests
To run the tests:
```
$ cd onyx/
$ python manage.py test -v 2
```
