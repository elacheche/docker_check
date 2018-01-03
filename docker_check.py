#!/usr/bin/env python3

"docker_check.py is a nagios compatible plugin to check docker containers."

import os
import re
import sys
import argparse

try:
    import docker
except ImportError as error:
    print("{}: Please install the docker module, you can use' \
          ''pip install docker' to do that".format(error))
    sys.exit(1)

__author__ = 'El Acheche Anis'
__license__ = 'GPL'
__version__ = '0.1'


def get_mem_pct(container, stats):
    '''Get a container memory usage in %'''
    mem = stats[container]['memory_stats']
    usage = mem['usage']
    limit = mem['limit']
    return round(usage * 100 / limit, 2)


def get_cpu_pct(container):
    '''Get a container cpu usage in % via docker stats cmd'''
    usage = str(
        os.popen("docker stats --no-stream=true " + container).read()
    ).split()
    usage_pct = usage[usage.index(container) + 1]
    return float(usage_pct[:-1])


def get_net_io(container, stats):
    '''Get a container Net In / Out usage since it's launche'''
    net = stats[container]['networks']
    net_in = net['eth0']['rx_bytes']
    net_out = net['eth0']['tx_bytes']
    return [net_in, net_out]


def get_disk_io(container, stats):
    '''Get a container Disk In / Out usage since it's launche'''
    disk = stats[container]['blkio_stats']['io_service_bytes_recursive']
    try:
        disk_in = disk[0]['value']
    except IndexError:
        disk_in = 0
    try:
        disk_out = disk[1]['value']
    except IndexError:
        disk_out = 0
    return disk_in, disk_out


def get_ct_stats(container, client):
    '''Get container status'''
    return client.containers.get(container).stats(stream=False)


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
    try:
        docker.from_env().containers.list()
        client = docker.from_env()
    except docker.errors.APIError as error:
        version = re.sub('[^0-9.]+', '',
                         str(error).split('server API version:')[1])
        client = docker.from_env(version=version)
    # Get list of running containers
    containers_list = client.containers.list()
    containers = []
    # If cid is True containers IDs will be used, otherwise names
    cid = False
    for i in containers_list:
        cid = str(i).replace('<', '').replace('>', '').split()[1]
        if cid:
            containers.append(cid)
        else:
            containers.append(
                os.popen("docker ps -f id=" + cid).read().split()[-1])
    # Get stats and metrics
    summary = ''
    stats = {}
    metrics = [0, 0]
    ct_stats = {}
    for i in containers:
        ct_stats[i] = get_ct_stats(i, client)
        mem_pct = get_mem_pct(i, ct_stats)
        cpu_pct = get_cpu_pct(i)
        net_in = get_net_io(i, ct_stats)[0]
        net_out = get_net_io(i, ct_stats)[1]
        disk_in = get_disk_io(i, ct_stats)[0]
        disk_out = get_disk_io(i, ct_stats)[1]
        stats[i + '_mem_pct'] = mem_pct
        stats[i + '_cpu_pct'] = cpu_pct
        summary += '{}_mem_pct={}% {}_cpu_pct={}% {}_net_in={} {}_net_out={} '\
                   '{}_disk_in={} {}_disk_out={} '.format(
                       i, mem_pct, i, cpu_pct, i, net_in, i, net_out, i,
                       disk_in, i, disk_out)
    # Get the highest % use
    for stat in stats:
        if stats[stat] >= metrics[1]:
            metrics[0] = stat
            metrics[1] = stats[stat]
    # Check stats values and output perfdata
    if metrics[1] < args.warning:
        print("OK | {}".format(summary))
        sys.exit(0)
    elif args.warning <= metrics[1] <= args.critical:
        print("WARNING: Some containers need your attention: {} have {}%'\
                    ' | {}".format(metrics[0], metrics[1], summary))
        sys.exit(1)
    elif metrics[1] > 80:
        print("CRITICAL: Some containers need your attention: {} have {}%'\
                    ' | {}".format(metrics[0], metrics[1], summary))
        sys.exit(2)
    else:
        print("UKNOWN | {}".format(summary))
        sys.exit(3)


if __name__ == '__main__':
    main()
