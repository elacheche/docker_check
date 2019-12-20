# docker_check.py
**Docker_check.py** is a nagios compatible plugin to check docker containers stats..

# Installation & Usage:
The current version don't need any arguments to be used all you need to do is:

## Install the Python3 library for the Docker Engine API:
```
pip3 install docker
```
Please check this [link](https://github.com/docker/docker-py) To get more information about this lib please check

## Get the script to the right path in the Docker server:

```
DOWNLOAD_URL=$(curl -s https://api.github.com/repos/elacheche/docker_check/releases/latest | awk '/browser_download_url/ {gsub("\"","");print $2}')
curl -Lso /usr/lib/nagios/plugins/docker_check.py $DOWNLOAD_URL
chmod +x /usr/lib/nagios/plugins/docker_check.py
```
You can find the package on the [Icinga Exchange](https://exchange.icinga.com/elacheche/Docker%20containers%20check/releases) as well, where you can download the latest release.

## Add nagios user to docker group:
```
sudo usermod -a -G docker nagios
```

## Configure the monitoring server:
In this section I'll illustrete how to setup the script to be used by [Icinga2](https://www.icinga.com/products/icinga-2/) via the *by_ssh* plugin..
Icinga2 is a Nagios fork, so the plugin is supposed to work with any Nagios fork, the sconfig files and syntax may change from a frok to an other

### Check command definition:
Edit */etc/icinga2/conf.d/commands.conf* and add:

```
object CheckCommand "check_docker_by_ssh" {
        import "by_ssh"
        vars.by_ssh_command = "/usr/lib/nagios/plugins/docker_check.py"
}
```
The script response time for 8 running containers is almost 30 seconds, please execute the script manually to make sure it don't exceeds 60 seconds, if it does, please add the following to the CheckCommand, replacing the values (in seconds) by the good ones:
```
        vars.by_ssh_timeout = 120 // Custom SSH connextion Timeout
        timeout = 120 // Custom execution Timeout
```

### Add service to Icinga:
Edit */etc/icinga2/conf.d/services/sshServices.conf* and add:
```
apply Service "docker_check_by_ssh" {
  import "generic-service"
  check_command = "check_docker_by_ssh"
  assign where (host.address || host.address6) && host.vars.os == "Linux" && host.name != NodeName && "docker" in host.vars.services
}
```
To not apply the docker_check script for all hosts we'll limit it to hosts that have a service called docker.

### Configure the hosts:
Edit */etc/icinga2/conf.d/hosts/foo.bar.com.conf* and add/change:
```
object Host "My Docker Server" {
  import "generic-host"
  address = "foo.bar"
  vars.os = "Linux"
  vars.services = ["docker"]
}
```

### Apply changes:
Check if everything is OK:
```
service icinga2 checkconfig
```
If so, restart Icinga:
```
service icinga2 restart
```
Otherwise fix the issues.

# Preview:
## Script output:
The script output should be similar to this:
```
OK | furious_ritchie_mem_pct=0.02% furious_ritchie_cpu_pct=0.0% furious_ritchie_net_in=91137 furious_ritchie_net_out=648 furious_ritchie_disk_in=1003520 furious_ritchie_disk_out=0 elated_booth_mem_pct=1.53% elated_booth_cpu_pct=1.73% elated_booth_net_in=556163 elated_booth_net_out=30239 elated_booth_disk_in=4423680 elated_booth_disk_out=58605568 
```
## Grafana:
This is a preview of the results I got with some testing containers (not the ones from the previous output), Icinga2 get checks from the script, Graphite get the data from Icinga then Grafana visualise them via Graphite.

![Status from Grafana](http://i.imgur.com/bxjcGJ1.png)

