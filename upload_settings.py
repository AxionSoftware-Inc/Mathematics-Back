
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    with client.open_sftp() as sftp:
        sftp.put('project/settings.py', '/root/var/www/Quantum-Uz-Backend/project/settings.py')
        print("Uploaded settings.py")
        
    stdin, stdout, stderr = client.exec_command("fuser -k 8000/tcp || true; cd /root/var/www/Quantum-Uz-Backend && venv/bin/python3 -m gunicorn project.wsgi:application --bind 127.0.0.1:8000 --daemon")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    run()
