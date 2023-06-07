# juststart (jst)  
  
A simple yet extensible cross-platform service manager.  
  
## Description  
  
juststart (shortened as jst) is a service management system aimed at replacing runit and systemctl service managers. It features intuitive scripts (including status hook scripts), script-based timers, flexible configurations, and user-friendly automation. In addition, it follows the principle of behavior as parameters, allowing users to use this service management system more naturally.  
  
  
## Features  
  
- User-friendly, following the KISS (Keep it simple) principle  
- Script-based timers  
- Flexible configurations and automation  
- Behavior as parameters  
- Can be used as an init system  
- Designed for cross-platform compatibility  
- Accepts other software (e.g., systemd, runit) as backends  
  
## Dependencies  
  
- Python standard library  
  
## Installation  
  
It is recommended to install using pip from GitHub:  
  
```bash  
pip install git+https://github.com/xz-dev/juststart.git  
```  
  
Or use tools like pipx for installation.  
  
## Usage  
  
1. Create a service directory:  
  
   ```bash
   mkdir ~/server  
   ```  
  
2. Start the juststart service:  
  
   ```bash
   juststart -c ~/server serve  
   ```  
  
3. Open a new terminal and use the following commands to add, manage, and view the service status:  
  
   ```bash
   jst -c ~/server add run.sh  
   jst -c ~/server status run  
   ``  
  
## Commands  
  
Here\'s a brief overview of the available commands:  
  
- `serve`: Run as a daemon  
- `add`: Add a service  
- `del`: Delete a service  
- `enable`: Enable a service  
- `disable`: Disable a service  
- `start`: Start a service  
- `restart`: Restart a service  
- `stop`: Stop a service  
- `reload`: Reload config for a service  
- `status`: Status of a service  
- `list`: List all services  
- `gc`: Garbage collect for stopped services  
- `shutdown`: Shutdown the daemon  
  
For more detailed information, refer to `jst --help`.  
  
## Roadmap  
  
1. Implement comprehensive testing, including unit tests and behavior tests.  
2. Add support for systemd and runit as backends.  
  
This project is currently under active development, and we welcome everyone to join the development process, submit code, or share ideas in the user community, on GitHub, or anywhere else.  
  
## Community and Communication  
  
To join the user community and communicate with other users, please join our Matrix room:  
  
[Matrix Room: #juststart:matrix.org](https://matrix.to/#/#juststart:matrix.org)  
  
Feel free to ask questions, share your experiences, and contribute to the project!  
