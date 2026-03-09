import paramiko
import sys

def ssh_exec(host, user, password, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=10)
        
        stdin, stdout, stderr = client.exec_command(command)
        
        print(stdout.read().decode())
        print(stderr.read().decode(), file=sys.stderr)
        
        client.close()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python ssh_exec.py host user password command")
        sys.exit(1)
    
    host = sys.argv[1]
    user = sys.argv[2]
    password = sys.argv[3]
    command = " ".join(sys.argv[4:])
    
    ssh_exec(host, user, password, command)
