
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    stdin, stdout, stderr = client.exec_command("cat /root/var/www/Quantum-Uz/package.json | grep '\"start\"'")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    run()
