
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    # Python script to run inside the shell
    python_cmd = """
from django.contrib.auth import get_user_model
User = get_user_model()
superusers = User.objects.filter(is_superuser=True)
if superusers.exists():
    for user in superusers:
        user.set_password('admin123')
        user.save()
        print(f'Password updated for: {user.username}')
else:
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser "admin" created with password "admin123"')
"""
    
    cmd = f"cd /root/var/www/Quantum-Uz-Backend && venv/bin/python3 manage.py shell -c \"{python_cmd}\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode(), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
