#!/usr/bin/env python3

"docker_check.py is a nagios compatible plugin to check docker containers."

import os
import re
import sys
import argparse

import logging
import queue
import threading

logging.basicConfig(
    format='%(asctime)s level=%(levelname)-7s '
           'threadName=%(threadName)s name=%(name)s %(message)s',
    level=logging.INFO
)

try:
    import docker
except ImportError as error:
    print("{}: Please install the docker module, you can use' \
          ''pip install docker' to do that".format(error))
    sys.exit(1)

__author__ = 'El Acheche Anis'
__license__ = 'GPLv3'
__version__ = '2018-06-04'


def get_ct_stats(container):
    '''Get container status'''
    return container.stats(stream=False)


def get_mem_pct(stats):
    '''Get a container memory usage in %'''
    try:
        usage = stats['memory_stats']['usage']
    except KeyError:
        usage = 0
    try:
        limit = stats['memory_stats']['limit']
    except KeyError:
        limit = 0
    try:
        return round(usage * 100 / limit, 2)
    except ZeroDivisionError:
        return 0


def get_cpu_pct(stats):
    '''Get a container cpu usage in %'''
    try:
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
            stats['precpu_stats']['cpu_usage']['total_usage']
    except KeyError:
        cpu_delta = 0
    try:
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
            stats['precpu_stats']['system_cpu_usage']
    except KeyError:
        system_delta = 0
    try:
        online_cpus = stats['cpu_stats']['online_cpus']
    except KeyError:
        try:
            online_cpus = len([item
                               for item in stats['cpu_stats']['percpu_usage']
                               if item > 0])
        except KeyError:
            online_cpus = 0
    if cpu_delta > 0 and system_delta > 0:
        return (cpu_delta / system_delta) * online_cpus * 100
    return 0.0


def get_net_io(stats):
    '''Get a container Net In / Out usage since it's launche'''
    try:
        net_in = stats['networks']['eth0']['rx_bytes']
    except KeyError:
        net_in = 0
    try:
        net_out = stats['networks']['eth0']['tx_bytes']
    except KeyError:
        net_out = 0
    return net_in, net_out


def get_disk_io(stats):
    '''Get a container Disk In / Out usage since it's launche'''
    disk = stats['blkio_stats']['io_service_bytes_recursive']
    try:
        disk_in = disk[0]['value']
    except IndexError:
        disk_in = 0
    except TypeError:
        disk_in = 0
    try:
        disk_out = disk[1]['value']
    except IndexError:
        disk_out = 0
    except TypeError:
        disk_out = 0
    return disk_in, disk_out


def get_ct_metrics(container_queue, containers_stats):
    '''Get container metrics from docker API'''
    logging.debug("Running get_ct_metrics()")
    while not container_queue.empty():
        container = container_queue.get()
        logging.debug("Get container %s stats", container.name)
        stats = get_ct_stats(container)

        mem_pct = get_mem_pct(stats)
        cpu_pct = get_cpu_pct(stats)
        net_in, net_out = get_net_io(stats)
        disk_in, disk_out = get_disk_io(stats)

        containers_stats['%s_mem_pct' % container.name] = mem_pct
        containers_stats['%s_cpu_pct' % container.name] = cpu_pct
        containers_stats['%s_net_in' % container.name] = net_in
        containers_stats['%s_net_out' % container.name] = net_out
        containers_stats['%s_disk_in' % container.name] = disk_in
        containers_stats['%s_disk_out' % container.name] = disk_out

        container_queue.task_done()
        logging.debug("Done with container %s stats", container.name)
    logging.debug("End get_ct_metrics()")


def get_ct_stats_message(containers_stats):
    '''Get check message from containers stats'''
    return ', '.join(
        [
            "%s have %.2f%%" % (k, v)
            for k, v
            in containers_stats.items()
        ]
    )


def get_ct_perfdata_message(containers_stats):
    '''Get perfdata message from containers stats'''
    return ' '.join(
        [
            "%s=%s" % (k, v)
            for k, v
            in containers_stats.items()
        ]
    )


def main():
    '''Scripts main function'''
    parser = argparse.ArgumentParser(description='Check docker processes.')
    parser.add_argument('-w', '--warning', type=int,
                        help='warning percentage (default 50)', default=50)
    parser.add_argument('-c', '--critical', type=int,
                        help='critcal percentage (default 80)', default=80)
    args = parser.parse_args()

    # Try to use the lastest API version otherwise use
    # the installed client API version
    # Get list of running containers
    try:
        containers_list = docker.from_env().containers.list()
        client = docker.from_env()
    except docker.errors.APIError as error:
        version = re.sub('[^0-9.]+', '',
                         str(error).split('server API version:')[1])
        client = docker.from_env(version=version)
        containers_list = client.containers.list()

    logging.debug("containers_list = %s", containers_list)

    # START
    containers_queue = queue.Queue()
    for container in containers_list:
        containers_queue.put(container)

    containers_stats = {}

    # Set up some threads to fetch the enclosures
    for th_id in range(len(containers_list)):
        worker = threading.Thread(
            target=get_ct_metrics,
            args=(containers_queue, containers_stats,),
            name='worker-{}'.format(th_id),
        )
        worker.setDaemon(True)
        worker.start()

    containers_queue.join()

    logging.debug("containers_stats = %s", containers_stats)
    stats = {
        k: v
        for k, v
        in containers_stats.items()
        if k.endswith('_mem_pct') or k.endswith('_cpu_pct')
    }
    logging.debug("stats = %s", stats)

    # Check stats values and output perfdata
    critical_ct = {k: v for k, v in stats.items() if v > args.critical}
    if critical_ct:
        print("CRITICAL: %s | %s" % (
            get_ct_stats_message(critical_ct),
            get_ct_perfdata_message(containers_stats)))
        sys.exit(2)

    warning_ct = {k: v for k, v in stats.items() if v > args.warning}
    if warning_ct:
        print("WARNING: %s | %s" % (
            get_ct_stats_message(warning_ct),
            get_ct_perfdata_message(containers_stats)))
        sys.exit(1)

    print("OK | %s" % get_ct_perfdata_message(containers_stats))
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        sys.exit(3)
