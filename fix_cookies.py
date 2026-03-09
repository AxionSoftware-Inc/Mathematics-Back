
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
            
        new_content = content.replace(
            'secure: process.env.NODE_ENV === "production"',
            'secure: false'
        )
        
        with sftp.file(file_path, 'w') as f:
            f.write(new_content)
    
    # Also need to do the same for any other places where cookies are set if any.
    # But for now this is the main one.
    
    print("Updated cookies to be non-secure for HTTP support.")
        
    client.close()

if __name__ == "__main__":
    run()
