
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
    echo "--- Port to Project Mapping ---"
    for port in {3000..3007}; do
        pid=$(netstat -tulpn | grep ":$port " | awk '{print $7}' | cut -d/ -f1)
        if [ ! -z "$pid" ]; then
            cwd=$(pwdx $pid | awk '{print $2}')
            echo "Port $port: PID $pid, CWD $cwd"
        fi
    done
    
    echo "\n--- Checking Quantum-Uz mode ---"
    cd /root/var/www/Quantum-Uz && grep -r "next dev" package.json
    """
    
    stdin, stdout, stderr = client.exec_command(script)
    print(stdout.read().decode('utf-8', errors='replace'))
    print(stderr.read().decode('utf-8', errors='replace'), file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    run()
