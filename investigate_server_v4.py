
import paramiko
import sys

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'
node_bin = '/root/.nvm/versions/node/v24.14.0/bin'
pm2_path = f'{node_bin}/pm2'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password)
        
        # Simpler commands
        script = f"""
        export PATH={node_bin}:$PATH
        echo "--- PM2 Status ---"
        {pm2_path} list || echo "PM2 not found or error"
        
        echo "--- Listening Ports and PIDs ---"
        netstat -tulpn | grep LISTEN | grep node || netstat -tulpn | grep LISTEN | grep next
        
        echo "--- Next processes command lines ---"
        ps -eo pid,ppid,pcpu,pmem,args | grep -E 'next|node|npm' | grep -v grep
        
        echo "--- Project directories ---"
        find /root/var/www/ -maxdepth 2 -type d
        """
        
        stdin, stdout, stderr = client.exec_command(script)
        print(stdout.read().decode())
        print(stderr.read().decode(), file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run()
