
import paramiko
import sys
import os

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

frontend_path = '/root/var/www/Quantum-Uz'
node_bin = '/root/.nvm/versions/node/v24.14.0/bin'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {host}...")
        client.connect(host, username=user, password=password)
        
        # 1. Sync files
        files_to_sync = [
            'app/(main)/academy/page.tsx',
            'app/(main)/library/page.tsx'
        ]
        
        with client.open_sftp() as sftp:
            for rel_path in files_to_sync:
                local_path = os.path.join(r'd:\Complete\Quantum uz', rel_path.replace('/', '\\'))
                remote_path = f"{frontend_path}/{rel_path}"
                print(f"Uploading {local_path} to {remote_path}...")
                sftp.put(local_path, remote_path)
        
        # 2. Build and Restart
        path_export = f'export PATH={node_bin}:$PATH'
        pm2_path = f'{node_bin}/pm2'
        
        commands = [
            f"cd {frontend_path} && {path_export} && npm run build",
            f"fuser -k 3000/tcp || true",
            f"cd {frontend_path} && {path_export} && {pm2_path} delete quantum-frontend || true",
            f"cd {frontend_path} && {path_export} && {pm2_path} start npm --name quantum-frontend -- start"
        ]
        
        for cmd in commands:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = client.exec_command(f"bash -l -c '{cmd}'")
            
            while True:
                line = stdout.readline()
                if not line: break
                try: print(line, end='')
                except UnicodeEncodeError: print(line.encode('ascii', errors='replace').decode(), end='')
            
            err = stderr.read().decode('utf-8', errors='ignore')
            if err: 
                try: print(f"Stderr: {err}")
                except UnicodeEncodeError: print(f"Stderr: {err.encode('ascii', errors='replace').decode()}")
            
        print("Frontend link fix deployment and restart completed.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run()
