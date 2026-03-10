
import paramiko
import sys

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'
node_bin = '/root/.nvm/versions/node/v24.14.0/bin'
pm2_path = f'{node_bin}/pm2'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)
    
    script = f"""
    export PATH={node_bin}:$PATH
    echo "--- PM2 Logs (last 50 lines) ---"
    {pm2_path} logs quantum-frontend --lines 50 --no-daemon
    """
    
    # Use a shorter version of logs command to not hang
    stdin, stdout, stderr = client.exec_command(f"export PATH={node_bin}:$PATH && {pm2_path} logs quantum-frontend --lines 50 --no-daemon & sleep 5; kill $!")
    
    print(stdout.read().decode('utf-8', errors='replace'))
    print(stderr.read().decode('utf-8', errors='replace'), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
