# mdb: A simple in memory DB

to run, clone the repo and run:

```
python mdb
```

from another shell:

``` sh
$ curl "127.0.0.1:8888/set?somekey=somevalue"
["success"]

$ curl "127.0.0.1:8888/get?somekey"
{"somekey": "somevalue"}

$ curl "127.0.0.1:8888/set?somekey=somevalue&someotherkey=someothervalue"
["success"]

$ curl "127.0.0.1:8888/get?somekey&someotherkey"
{"somekey": "somevalue", "someotherkey": "someothervalue"}
```

