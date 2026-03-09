
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    file_path = '/root/var/www/Quantum-Uz/app/admin-login/actions.ts'
    
    with client.open_sftp() as sftp:
        with sftp.file(file_path, 'r') as f:
            content = f.read().decode('utf-8')
            
        # Add a log
        if 'console.log("Login result:",' not in content:
            new_content = content.replace(
                'const data = await res.json();',
                'const data = await res.json();\n        console.log("Login response data:", data);'
            )
            with sftp.file(file_path, 'w') as f:
                f.write(new_content)
    
    print("Added debug logging to actions.ts")
    client.close()

if __name__ == "__main__":
    run()
