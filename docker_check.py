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

def main():
	client=docker.from_env(version="1.21") #try except the version based on docker version | grep "server api"
	ls=client.containers.list()
	ct=[]
	for i in ls:
		ct.append(str(i).replace('<','').replace('>','').split()[1])
	#cl=client.containers.get("3f106f3328")
	for i in ct:
		print(client.containers.get(i).stats(stream=False)['networks'])


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
