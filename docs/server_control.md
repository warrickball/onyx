# Server Control

**Start the server:**
```
$ cd onyx/
$ gunicorn -c onyx.gunicorn.py
```

**Stop the server:**
```
$ pkill -f onyx.gunicorn.py
```

**View access logs:**
```
$ tail -f logs/access.log
```

**View error logs:**
```
$ tail -f logs/error.log
```