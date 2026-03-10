
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
    
    # We will kill everything on ports 3000-3007 and 8000, then restart what's needed.
    cleanup_script = f"""
    export PATH={node_bin}:$PATH
    
    echo "--- Stopping PM2 ---"
    {pm2_path} stop all || true
    {pm2_path} delete all || true
    
    echo "--- Killing processes on ports 3000-3007 ---"
    for port in {{3000..3007}}; do
        fuser -k $port/tcp || true
    done
    
    echo "--- Killing processes on port 8000 ---"
    fuser -k 8000/tcp || true
    
    echo "--- Double checking for runaway node processes ---"
    pkill -9 node || true
    pkill -9 next-server || true
    
    echo "--- Restarting Backend (Gunicorn) ---"
    cd /root/var/www/Quantum-Uz-Backend && venv/bin/python3 -m gunicorn project.wsgi:application --bind 127.0.0.1:8000 --disable-redirect-access-to-syslog --daemon
    
    echo "--- Restarting Main Frontend (Quantum-Uz) in PROD mode ---"
    cd /root/var/www/Quantum-Uz && {pm2_path} start npm --name "quantum-frontend" -- start
    
    echo "--- Final Process Check ---"
    ps aux --sort=-%cpu | head -n 10
    echo "--- Listening Ports ---"
    netstat -tulpn | grep LISTEN | grep -E 'node|next|python'
    """
    
    stdin, stdout, stderr = client.exec_command(cleanup_script)
    print(stdout.read().decode('utf-8', errors='replace'))
    error = stderr.read().decode('utf-8', errors='replace')
    if error:
        print("--- Stderr ---")
        print(error)
        
    client.close()

if __name__ == "__main__":
    run()
