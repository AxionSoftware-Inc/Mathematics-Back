
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    node_bin = '/root/.nvm/versions/node/v24.14.0/bin'
    pm2_path = f'{node_bin}/pm2'
    path_export = f'export PATH={node_bin}:\$PATH'
    
    commands = [
        "fuser -k 3000/tcp || true",
        f"{path_export} && {pm2_path} delete quantum-frontend || true",
        f"cd /root/var/www/Quantum-Uz && {path_export} && {pm2_path} start npm --name quantum-frontend -- start"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        # Don't print output to avoid encoding issues, just status
        stdout.read()
        err = stderr.read().decode('utf-8', errors='ignore')
        if err: print(f"Stderr: {err}")
        
    client.close()

if __name__ == "__main__":
    run()
