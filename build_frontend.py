
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
    
    # Ensure .env has local API_URL for server-side fetches
    # And relative for client side if possible, or just the IP
    env_content = "NEXT_PUBLIC_API_URL=http://62.72.32.37\n"
    
    with client.open_sftp() as sftp:
        with sftp.file('/root/var/www/Quantum-Uz/.env', 'w') as f:
            f.write(env_content)
    
    commands = [
        f"cd /root/var/www/Quantum-Uz && {path_export} && npm run build",
        f"fuser -k 3000/tcp || true",
        f"cd /root/var/www/Quantum-Uz && {path_export} && {pm2_path} delete quantum-frontend || true",
        f"cd /root/var/www/Quantum-Uz && {path_export} && {pm2_path} start npm --name quantum-frontend -- start"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        
        # Build can take time, so we read it
        while True:
            line = stdout.readline()
            if not line: break
            print(line, end='')
            
        err = stderr.read().decode('utf-8', errors='ignore')
        if err: print(f"Stderr: {err}")
        
    client.close()

if __name__ == "__main__":
    run()
