
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    script = """
import os
import django
import sys

# Add the project directory to sys.path
sys.path.append('/root/var/www/Quantum-Uz-Backend')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
for u in User.objects.all():
    print(f'User: {u.username}, Email: {u.email}, Super: {u.is_superuser}')
"""
    with client.open_sftp() as sftp:
        with sftp.file('/tmp/list_users.py', 'w') as f:
            f.write(script)
            
    cmd = "cd /root/var/www/Quantum-Uz-Backend && venv/bin/python3 /tmp/list_users.py"
    
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode(), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
