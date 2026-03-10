
import paramiko
import sys

# Set standard output encoding to utf-8
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
    output = stdout.read().decode('utf-8', errors='replace')
    error = stderr.read().decode('utf-8', errors='replace')
    
    print(output)
    if error:
        print("--- Errors ---")
        print(error)
        
    client.close()

if __name__ == "__main__":
    run()
