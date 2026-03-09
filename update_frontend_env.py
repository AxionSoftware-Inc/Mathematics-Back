
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    # Update .env for frontend
    env_content = "NEXT_PUBLIC_API_URL=http://62.72.32.37\n"
    
    with client.open_sftp() as sftp:
        with sftp.file('/root/var/www/Quantum-Uz/.env', 'w') as f:
            f.write(env_content)
    
    # Restart Next.js app. 
    # Need to find how it's running. Using pkill and restarting or using PM2 if found.
    # Earlier I couldn't find PM2 in path but it existed in /root/.nvm/...
    
    # Let's try to just kill the process and start npm start in background.
    pm2_path = '/root/.nvm/versions/node/v24.14.0/bin/pm2'
    path_export = 'export PATH=/root/.nvm/versions/node/v24.14.0/bin:$PATH'
    
    commands = [
        f"cd /root/var/www/Quantum-Uz && {path_export} && {pm2_path} stop quantum-frontend || true",
        f"cd /root/var/www/Quantum-Uz && {path_export} && {pm2_path} delete quantum-frontend || true",
        f"cd /root/var/www/Quantum-Uz && {path_export} && {pm2_path} start 'npm start' --name quantum-frontend"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode(), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
