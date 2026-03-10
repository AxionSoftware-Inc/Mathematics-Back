
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
    echo "--- Total Memory ---"
    free -h
    echo "\n--- CPU Usage (Snapshot) ---"
    uptime
    echo "\n--- Disk Space ---"
    df -h /
    """
    
    stdin, stdout, stderr = client.exec_command(script)
    print(stdout.read().decode('utf-8', errors='replace'))
    client.close()

if __name__ == "__main__":
    run()
