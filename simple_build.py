
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
    path_export = f'export PATH={node_bin}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:\$PATH'
    
    print("Starting build...")
    stdin, stdout, stderr = client.exec_command(f"cd /root/var/www/Quantum-Uz && {path_export} && npm run build")
    
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    
    print("Build output:")
    print(out)
    if err: print("Build errors:", err)
    
    client.close()

if __name__ == "__main__":
    run()
