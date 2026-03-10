
import paramiko
import sys

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    script = """
    echo "--- Nginx Sites Enabled ---"
    ls /etc/nginx/sites-enabled/
    
    echo "\n--- Checking Shakhrisabz and Architecture package.json ---"
    cat /root/var/www/Shakhrisabz/package.json | grep scripts -A 10 || echo "No Shakhrisabz"
    cat /root/var/www/Architecture/package.json | grep scripts -A 10 || echo "No Architecture"
    """
    
    stdin, stdout, stderr = client.exec_command(script)
    print(stdout.read().decode('utf-8', errors='replace'))
    print(stderr.read().decode('utf-8', errors='replace'), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
