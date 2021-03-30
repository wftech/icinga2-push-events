#!/usr/bin/env python
import json
import random

from faker import Faker
import redis
import time

NUM_HOSTS = 10
NUM_SERVICES = 10
NUM_ITEMS = 1000

redis_client = redis.Redis(host='localhost', port=6379, db=0)
fake = Faker()

host_names = []
for i in range(NUM_HOSTS):
    host_names.append(fake.hostname(levels=1))
svc_names = []
for i in range(NUM_SERVICES):
    svc_names.append(fake.slug())


# generate some
#while True:
for i in range(NUM_ITEMS):
    state = random.randint(0, 3)
    if state == 0:
        msg = 'OK'
    elif state == 1:
        msg = 'Warning - it should be checked'
    elif state == 2:
        msg = 'CRITICAL - it is broken'
    else:
        msg = 'UNKNOWN'

    record = dict(
        hostname=random.choice(host_names),
        service=random.choice(svc_names),
        state=state,
        msg=msg
    )
    record_b = bytes(json.dumps(record), encoding='utf-8')
    print(json.dumps(record))
    # push to the end of the list
    redis_client.rpush('riemann', record_b)
    #time.sleep(10)

