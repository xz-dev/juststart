# juststart
A simple yet extensible cross-platform service manager.  

Not fully tested yet, but you can try it for fun.  

## Use
```bash
$ juststart --help
usage: jst [-h] [--address ADDRESS] [--port PORT] [--password PASSWORD] [--config CONFIG] {serve,add,del,enable,disable,start,restart,stop,reload_config,status,list,gc,shutdown} ...

A simple yet extensible cross-platform service manager

positional arguments:
  {serve,add,del,enable,disable,start,restart,stop,reload_config,status,list,gc,shutdown}
                        Available commands
    serve               Run as a daemon
    add                 Add a service
    del                 Delete a service
    enable              Enable a service
    disable             Disable a service
    start               Start a service
    restart             Restart a service
    stop                Stop a service
    reload_config       Reload config for a service
    status              Status of a service
    list                List all services
    gc                  Garbage collect for stoped services
    shutdown            Shutdown Daemon

options:
  -h, --help            show this help message and exit
  --address ADDRESS, --addr ADDRESS
                        Service manager listen address
  --port PORT, -p PORT  Service manager listen port number
  --password PASSWORD   Service manager password
  --config CONFIG, -c CONFIG
                        Path to config file

```
