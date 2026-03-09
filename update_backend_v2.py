
import paramiko
import sys
import os

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

nginx_config = r'''server {
    listen 80;
    server_name 62.72.32.37;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /django-admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/quantum_backend_static/;
    }

    location /media/ {
        alias /var/www/quantum_backend_media/;
    }
}
'''

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    with client.open_sftp() as sftp:
        # Upload Nginx config
        with sftp.file('/etc/nginx/sites-available/default', 'w') as f:
            f.write(nginx_config)
            
        # Upload updated files
        sftp.put('project/urls.py', '/root/var/www/Quantum-Uz-Backend/project/urls.py')
        sftp.put('project/settings.py', '/root/var/www/Quantum-Uz-Backend/project/settings.py')
    
    commands = [
        "nginx -t && systemctl reload nginx",
        "mkdir -p /var/www/quantum_backend_static /var/www/quantum_backend_media",
        "cp -r /root/var/www/Quantum-Uz-Backend/static/* /var/www/quantum_backend_static/ || true",
        "cp -r /root/var/www/Quantum-Uz-Backend/media/* /var/www/quantum_backend_media/ || true",
        "chown -R www-data:www-data /var/www/quantum_backend_static /var/www/quantum_backend_media",
        "chmod -R 755 /var/www/quantum_backend_static /var/www/quantum_backend_media",
        "fuser -k 8000/tcp || true",
        "cd /root/var/www/Quantum-Uz-Backend && venv/bin/python3 -m gunicorn project.wsgi:application --bind 127.0.0.1:8000 --daemon"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode(), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
