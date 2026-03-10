
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

pm2_path = '/root/.nvm/versions/node/v24.14.0/bin/pm2'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {host}...")
        client.connect(host, username=user, password=password)
        
        commands = [
            f"{pm2_path} list",
            "ls -R /root/var/www/ | grep ':'", # List directories to find projects
            "ps -ef | grep next-server", # Show full command line for next-servers
            "cat /etc/nginx/sites-enabled/default" # Check nginx routing
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err: print(f"Error: {err}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run()
