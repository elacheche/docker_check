#!/usr/bin/env python3
import sys
import os
import docker
import json
import logging

logger = logging.getLogger()
__author__ = ''
__copyright__ = ''
__credits__ = ['']
__license__ = ''
__version__ = ''

'''
Requires Python 3

Dummy Data:
CONTAINER           CPU %               MEM USAGE / LIMIT    MEM %               NET I/O             BLOCK I/O
drunk_leakey        0.12%               13.19 MB / 6.15 GB   0.21%               122 MB / 3.65 MB    498.9 MB / 134.7 MB

'''


client=docker.from_env(version="1.21") #try except the version based on docker version | grep "server api"
ls=client.containers.list()
ct=[]
for i in ls:
	ct.append(str(i).replace('<','').replace('>','').split()[1])

def get_mem_pct(ct):
	mem=client.containers.get(ct).stats(stream=False)['memory_stats']
	usage=mem['usage']
	limit=mem['limit']
	return round(usage*100/limit,2)
	
def get_cpu_pct(ct):
	#cpu=client.containers.get(ct).stats(stream=False)['precpu_stats']
	#usage=cpu['system_cpu_usage']
	# ToDo:
	# Use API instead of docker stats
	# (new-docker-usage - old-docker-usage) / (new-system-cpu-usage - old-cpu-usage) * 100
	# with spreding that on CPU CORE numbers
	# should find a way to keep ODU & OCU values : OS STATS LOGS or usa a tmp file
	usage=str(os.popen("docker stats --no-stream=true "+ct).read()).split()
	usage_pct=usage[usage.index(ct)+1]
	return usage_pct[:-1]




def main():
	#print(str(sys.argv))
#	arg=sys.argv[1]
	#print(arg)
##	client=docker.from_env(version="1.21") #try except the version based on docker version | grep "server api"
##	ls=client.containers.list()
##	ct=[]
##	for i in ls:
##		ct.append(str(i).replace('<','').replace('>','').split()[1])
	#cl=client.containers.get("3f106f3328")
	for i in ct:
		#print(client.containers.get(i).stats(stream=False)[arg])
		print('{} → {}'.format(i, get_mem_pct(i)))
		print('{} → {}'.format(i, get_cpu_pct(i)))
#		for j,k in client.containers.get(i).stats(stream=False).items():
#			print(j)

'''
used_space=os.popen("df -h / | grep -v Filesystem | awk '{print $5}'").readline().strip()

if used_space < "85%":
        print("OK - {} of disk space used.".format(used_space))
        sys.exit(0)
elif used_space == "85%":
        print("WARNING - {} of disk space used.".format(used_space))
        sys.exit(1)
elif used_space > "85%":
        print("CRITICAL - {} of disk space used.".format(used_space))
        sys.exit(2)
else:
        print("UKNOWN - {} of disk space used.".format(used_space))
        sys.exit(3)
'''
if __name__ == '__main__':
	## Initialize logging before hitting main, in case we need extra debuggability
	#log.basicConfig(level=log.DEBUG, format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
	main()
