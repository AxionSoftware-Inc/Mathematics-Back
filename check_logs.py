
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    # Check for Gunicorn logs or just try to run it in foreground for a bit or check journal?
    # Since I started it with --daemon, let's see if we can find where it logs.
    # Usually it doesn't log to a file unless specified.
    
    # Let's try to check the Nginx access logs to see the POST requests
    commands = [
        "tail -n 20 /var/log/nginx/access.log",
        "tail -n 20 /var/log/nginx/error.log",
        "ls -la /root/var/www/Quantum-Uz/.env" # Check frontend env
    ]
    
    for cmd in commands:
        print(f"--- Running: {cmd} ---")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode(), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
