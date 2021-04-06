#!/usr/bin/env python3
import json
import os
import time
import sys

from icinga2api.client import Client as Icinga2Client
from icinga2api.exceptions import Icinga2ApiException
import redis

import warnings

from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', category=InsecureRequestWarning)

ICINGA_API_CONFIG = os.getenv('ICINGA2_CONFIG', 'icinga2-api.ini')
ONE_SHOT_SYNC = int(os.getenv('ONE_SHOT_SYNC', 0))
REDIS_KEY = os.getenv('REDIS_KEY', 'riemann')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
WORKER_THREADS_COUNT = int(os.getenv('THREAD_COUNT', 4))
MESSAGE_COUNTER = 0

icinga2api = Icinga2Client(config_file=ICINGA_API_CONFIG)


def process_messages():
    """
    Process all messages
    :return:
    """
    while True:
        status = process_one_msg()
        if ONE_SHOT_SYNC and not status:
            break


def process_one_msg():
    """
    Pop one message from redis and push it to Icinga

    :return:    True if some message was processed
                None other case
    """
    global MESSAGE_COUNTER

    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    item = redis_client.blpop(REDIS_KEY, timeout=5)
    if item:
        _, obj = item
    else:
        return None
    event = json.loads(str(obj, encoding='utf-8'))

    host_name, svc_name = event['hostname'], event['service']

    # push result
    exit_status = event['state']
    plugin_output = event['msg']
    try:
        res = icinga2api.actions.process_check_result(
            object_type='Service',
            name=f'{host_name}!{svc_name}',
            exit_status=exit_status,
            plugin_output=plugin_output,
            check_command='push',
            check_source='push',
        )
    except Icinga2ApiException:
        res = None
    if res:
        MESSAGE_COUNTER += 1
        return True

    # create host
    try:
        icinga2api.objects.create(
            object_type='Host',
            name=host_name,
            attrs=dict(
                check_command='passive',
                templates=[],
                enable_active_checks=False,
                address="127.0.0.1",
                vars=dict(
                    autocreated=True
                ),
            )
        )
    except Icinga2ApiException:
        pass
    host_obj = icinga2api.objects.get('Host', name=host_name)
    assert host_obj

    # create service
    try:
        icinga2api.objects.create(
            object_type='Service',
            name=f'{host_name}!{svc_name}',
            attrs=dict(
                check_command='passive',
                host_name=host_name,
                templates=[],
                enable_active_checks=False,
                vars=dict(
                    autocreated=True,
                ),
            )
        )
    except Icinga2ApiException:
        pass
    # ensure object is created
    icinga2api.objects.get('Service', name=f'{host_name}!{svc_name}')

    # retry push
    icinga2api.actions.process_check_result(
        object_type='Service',
        name=f'{host_name}!{svc_name}',
        exit_status=exit_status,
        plugin_output=plugin_output,
        check_command='push',
        check_source='push',
    )
    MESSAGE_COUNTER += 1
    # message was processed
    return True


if __name__ == '__main__':
    import threading

    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    redis_client.ping()

    for n in range(WORKER_THREADS_COUNT):
        worker = threading.Thread(target=process_messages, args=[],
                                  daemon=True, name=f'worker-{n}')
        worker.start()
    time_start = time.time()
    while True:
        messages_left = redis_client.llen(REDIS_KEY)
        rate = int(MESSAGE_COUNTER / (time.time() - time_start))
        status_msg = f'events processed:{MESSAGE_COUNTER:<8}  left:{messages_left:<8}  rate:{rate:<8d} ev/s'
        if os.isatty(sys.stdout.fileno()):
            print(status_msg, end='\r')
            time.sleep(1)
        else:
            print(status_msg)
            time.sleep(15)
        sys.stdout.flush()
        if ONE_SHOT_SYNC and not messages_left:
            break
        #
        if threading.active_count() < WORKER_THREADS_COUNT:
            print("Some threads died. Giving up.")
            raise SystemExit(2)
    print("Finished")
