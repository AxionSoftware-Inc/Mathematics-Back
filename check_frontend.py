
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    commands = [
        "netstat -tulnp | grep 3000",
        "find /root/var/www/Quantum-Uz -maxdepth 2 -name '.env*'",
        "grep -r 'BASE_URL' /root/var/www/Quantum-Uz/src --include='*.ts' --include='*.tsx' | head -n 20",
        "grep -r 'api' /root/var/www/Quantum-Uz/src --include='*.ts' --include='*.tsx' | grep 'http' | head -n 20",
        "cat /root/var/www/Quantum-Uz/package.json"
    ]
    
    for cmd in commands:
        print(f"--- Running: {cmd} ---")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode(), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
