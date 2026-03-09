
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        print("Connected")
        
        # Upload urls.py
        with client.open_sftp() as sftp:
            sftp.put('project/urls.py', '/root/var/www/Quantum-Uz-Backend/project/urls.py')
            print("Uploaded urls.py")
            
        cmds = [
            "mkdir -p /var/www/quantum_backend_static /var/www/quantum_backend_media",
            "cp -r /root/var/www/Quantum-Uz-Backend/static/* /var/www/quantum_backend_static/ || true",
            "cp -r /root/var/www/Quantum-Uz-Backend/media/* /var/www/quantum_backend_media/ || true",
            "chown -R www-data:www-data /var/www/quantum_backend_static /var/www/quantum_backend_media",
            "chmod -R 755 /var/www/quantum_backend_static /var/www/quantum_backend_media",
            "fuser -k 8000/tcp || true",
            "cd /root/var/www/Quantum-Uz-Backend && venv/bin/python3 -m gunicorn project.wsgi:application --bind 127.0.0.1:8000 --daemon"
        ]
        
        for c in cmds:
            stdin, stdout, stderr = client.exec_command(c)
            print(f"Cmd: {c}")
            print(stdout.read().decode())
            print(stderr.read().decode())
            
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
