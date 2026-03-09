
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    cmd = 'cat /root/.pm2/logs/quantum-frontend-error.log'
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Read binary and decode with ignore
    data = stdout.read()
    print(data.decode('utf-8', errors='ignore'))
        
    client.close()

if __name__ == "__main__":
    run()
