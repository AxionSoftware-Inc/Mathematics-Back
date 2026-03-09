
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    python_cmd = """
from django.contrib.auth import get_user_model
User = get_user_model()
for u in User.objects.all():
    print(f'User: {u.username}, Email: {u.email}, Super: {u.is_superuser}')
"""
    
    cmd = f"cd /root/var/www/Quantum-Uz-Backend && venv/bin/python3 manage.py shell -c \"{python_cmd}\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode(), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
