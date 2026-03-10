
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    node_bin = '/root/.nvm/versions/node/v24.14.0/bin'
    pm2_path = f'{node_bin}/pm2'
    
    script = f"""
    export PATH={node_bin}:$PATH
    echo "--- PM2 Status ---"
    {pm2_path} list
    echo "--- Listening Ports ---"
    netstat -tulpn | grep LISTEN | grep -E 'node|next'
    echo "--- High CPU Processes ---"
    ps aux --sort=-%cpu | head -n 10
    """
    
    stdin, stdout, stderr = client.exec_command(script)
    print(stdout.read().decode())
    print(stderr.read().decode(), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
