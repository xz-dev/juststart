# juststart
A simple yet extensible cross-platform service manager.  

Not tested yet, do not use now.  

## Use
```bash
$ juststart --help
usage: juststart [-h] [--address ADDRESS] [--port PORT] [--password PASSWORD]
                 [--config CONFIG]
                 {add,del,enable,disable,start,restart,stop,reload_config,status}
                 ...

A simple yet extensible cross-platform service manager

optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS, --addr ADDRESS
                        Service manager listen address (default: localhost)
  --port PORT, -p PORT  Service manager listen port number (default: 50000)
  --password PASSWORD   Service manager password
  --config CONFIG, --conf CONFIG
                        Path to config file

Available commands:
  {add,del,enable,disable,start,restart,stop,reload_config,status}
    add                 Add a service
    del                 Delete a service
    enable              Enable a service
    disable             Disable a service
    start               Start a service
    restart             Restart a service
    stop                Stop a service
    reload_config       Reload config for a service
    status              Status of a service
```
