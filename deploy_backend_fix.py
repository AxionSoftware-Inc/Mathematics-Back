
import paramiko
import sys
import os

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

backend_path = '/root/var/www/Quantum-Uz-Backend'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {host}...")
        client.connect(host, username=user, password=password)
        
        # 1. Git pull
        print("Running git pull...")
        stdin, stdout, stderr = client.exec_command(f"cd {backend_path} && git pull")
        print(stdout.read().decode())
        print(stderr.read().decode(), file=sys.stderr)
        
        # 2. Upload the fixed views.py
        local_views_path = r'd:\Complete\Quantum uz\Quantum uz backend\application\views.py'
        remote_views_path = f"{backend_path}/application/views.py"
        
        print(f"Uploading {local_views_path} to {remote_views_path}...")
        with client.open_sftp() as sftp:
            sftp.put(local_views_path, remote_views_path)
            
        # 3. Restart commands
        commands = [
            f"cd {backend_path} && venv/bin/python3 manage.py migrate",
            f"cd {backend_path} && venv/bin/python3 manage.py collectstatic --noinput",
            "fuser -k 8000/tcp || true",
            f"cd {backend_path} && venv/bin/python3 -m gunicorn project.wsgi:application --bind 127.0.0.1:8000 --disable-redirect-access-to-syslog --daemon"
        ]
        
        for cmd in commands:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            if out: print(out)
            if err: print(err, file=sys.stderr)
            
        print("Backend deployment and restart completed.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run()
