
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {host}...")
        client.connect(host, username=user, password=password)
        
        commands = [
            "top -b -n 1 | head -n 20", # Current CPU/Mem usage
            "ps aux --sort=-%cpu | head -n 10", # Top CPU consuming processes
            "pm2 list", # PM2 status
            "pm2 show all", # More details on PM2 processes
            "free -h", # Memory usage
            "df -h", # Disk usage
            "netstat -tulpn | grep LISTEN" # Listening ports
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err: print(f"Error: {err}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run()
