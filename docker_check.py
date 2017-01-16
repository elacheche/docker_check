#!/usr/bin/env python3
import os
import re
import sys
try:
	import docker
except ImportError as e:
	print("{}: Please install the docker module, you can use 'pip install docker' to do that".format(e))
	sys.exit(1)
	
__author__ = 'El Acheche Anis'
__license__ = 'GPL'
__version__ = '0.1'


def get_mem_pct(ct, stats):
    '''Get a container memory usage in %'''
    mem = stats[ct]['memory_stats']
    usage = mem['usage']
    limit = mem['limit']
    return round(usage*100/limit, 2)


def get_cpu_pct(ct):
    '''Get a container cpu usage in % via docker stats cmd'''
    usage = str(os.popen("docker stats --no-stream=true "+ct).read()).split()
    usage_pct = usage[usage.index(ct)+1]
    return float(usage_pct[:-1])


def get_net_io(ct, stats):
    '''Get a container Net In / Out usage since it's launche'''
    net = stats[ct]['networks']
    net_in = net['eth0']['rx_bytes']
    net_out = net['eth0']['tx_bytes']
    return [net_in, net_out]


def get_disk_io(ct, stats):
    '''Get a container Disk In / Out usage since it's launche'''
    disk = stats[ct]['blkio_stats']['io_service_bytes_recursive']
    disk_in = disk[0]['value']
    disk_out = disk[1]['value']
    return disk_in, disk_out


def main():
    '''Try to use the lastest API version otherwise use
    the installed client API version
    '''
    try:
        docker.from_env().containers.list()
        client = docker.from_env()
    except docker.errors.APIError as e:
        v = re.sub('[^0-9.]+', '', str(e).split('server API version:')[1])
        client = docker.from_env(version=v)
    '''Get list of running containers'''
    ls = client.containers.list()
    ct = []
    for i in ls:
        ct.append(str(i).replace('<', '').replace('>', '').split()[1])
    '''Get stats and metrics'''
    summary = ''
    stats = {}
    metrics = [0, 0]
    ct_stats = {}
    for i in ct:
        ct_stats[i] = client.containers.get(i).stats(stream=False)
        mem_pct = get_mem_pct(i, ct_stats)
        cpu_pct = get_cpu_pct(i)
        net_in = get_net_io(i, ct_stats)[0]
        net_out = get_net_io(i, ct_stats)[1]
        disk_in = get_disk_io(i, ct_stats)[0]
        disk_out = get_disk_io(i, ct_stats)[1]
        stats[i+'_mem_pct'] = mem_pct
        stats[i+'_cpu_pct'] = cpu_pct
        summary += '{}_mem_pct={}% {}_cpu_pct={}% {}_net_in={} {}_net_out={} '\
                   '{}_disk_in={} {}_disk_out={} '.format(
                    i, mem_pct, i, cpu_pct, i, net_in, i, net_out, i, disk_in,
                    i, disk_out)
    '''Get the highest % use'''
    for s in stats:
        if stats[s] >= metrics[1]:
            metrics[0] = s
            metrics[1] = stats[s]
    '''Check stats values and output perfdata'''
    if metrics[1] < 50:
            print("OK | {}".format(summary))
            sys.exit(0)
    elif 50 <= metrics[1] <= 80:
            print("WARNING: Some containers need your attention: {} have {}% '\
                    | {}".format(metrics[0], metrics[1], summary))
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
