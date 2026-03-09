
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    pm2_path = '/root/.nvm/versions/node/v24.14.0/bin/pm2'
    path_export = 'export PATH=/root/.nvm/versions/node/v24.14.0/bin:$PATH'
    
    cmd = f"{path_export} && {pm2_path} logs quantum-frontend --lines 100 --no-colors"
    
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Use a safe way to handle potential unicode
    out = stdout.read().decode('utf-8', errors='replace')
    print(out)
        
    client.close()

if __name__ == "__main__":
    run()
