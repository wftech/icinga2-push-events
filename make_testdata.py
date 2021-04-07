#!/usr/bin/env python3
import json
import random
import os
import sys

from faker import Faker

import redis
import time

REDIS_KEY = os.getenv('REDIS_KEY', 'riemann')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# how many hosts and services should we generate
FAKE_HOST_COUNT = int(os.getenv('FAKE_HOST_COUNT', '10'))
FAKE_SERVICES_COUNT = int(os.getenv('FAKE_SERVICES_COUNT', '10'))

# how many statuses should we generate
FAKE_STATUSES_COUNT = int(os.getenv('FAKE_STATUSES_COUNT', '1000'))

# delay between two pushes
INTER_PUSH_DELAY = float(os.getenv('INTER_PUSH_DELAY', '0.1'))


redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
fake = Faker()

host_names = []
for i in range(FAKE_HOST_COUNT):
    host_names.append(fake.hostname(levels=1))
svc_names = []
for i in range(FAKE_SERVICES_COUNT):
    svc_names.append(fake.slug())


messages_to_push = []
for i in range(FAKE_STATUSES_COUNT):
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
    messages_to_push.append(record)

messages_pushed = 0
last_status = 0
time_start = time.time()
while messages_to_push:
    record_b = bytes(json.dumps(messages_to_push.pop()), encoding='utf-8')
    # push to the end of the list
    redis_client.rpush(REDIS_KEY, record_b)
    time.sleep(INTER_PUSH_DELAY)
    #
    messages_pushed += 1
    messages_left = len(messages_to_push)
    rate = (messages_pushed / (time.time() - time_start))

    # add status message
    if os.isatty(sys.stdout.fileno()):
        status_delay = 1
        eol = '\r'
    else:
        status_delay = 15
        eol = '\n'

    # show status message periodically or on end of processing
    if time.time() - last_status > status_delay or not messages_to_push:
        status_msg = f'events pushed:{messages_pushed:<8}  left to push:{messages_left:<8}  rate:{rate:<8.1f} ev/s'
        print(status_msg, end=eol)
        sys.stdout.flush()
        last_status = time.time()
print('\nPush completed')

