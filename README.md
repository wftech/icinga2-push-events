
# Icinga push status

This is proof of concept daemon reading monitoring events
from Redis and pushing them to Icinga with API.

It is not production ready (at the moment).

## How to start


* Get the container `ghcr.io/wftech/icinga2-push-events/icinga2-push-events:build`

* provide config file `icinga2_api.ini` (or use example)

* provide env vars

    ICINGA2_CONFIG - path to `icinga2_api.ini`
    
    ONE_SHOT_SYNC - 0 (default) or 1. If set to one, script just runs
    
    REDIS_KEY - `riemann` (default). key to check
    
    REDIS_HOST, REDIS_PORT, REDIS_DB - `localhost`, `6379` and `0` - connection to redis
    
    WORKER_THREADS_COUNT - `4` - number of threads to do the work
  
* start the container



## how to test

There is testing image
`ghcr.io/wftech/icinga2-push-events/icinga2-push-events:testdata` which 
generates test events and pushes them into Redis

Feel  free to use `docker-compose` for testing.

