
import paramiko
import sys
import json

host = '62.72.32.37'
user = 'root'
password = 'Aa7161062.123'
pm2_path = '/root/.nvm/versions/node/v24.14.0/bin/pm2'

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password)
        
        # 1. Get PM2 list in JSON
        stdin, stdout, stderr = client.exec_command(f"{pm2_path} jlist")
        pm2_data = stdout.read().decode()
        print("\n--- PM2 JLIST ---")
        try:
            processes = json.loads(pm2_data)
            for p in processes:
                print(f"Name: {p['name']}, Status: {p['pm2_env']['status']}, CPU: {p['monit']['cpu']}%, Mem: {p['monit']['memory']} bytes, App Path: {p['pm2_env']['pm_cwd']}")
        except:
            print(pm2_data)

        # 2. Check for dev mode processes by looking at command lines
        print("\n--- Command Lines for Next.js ---")
        stdin, stdout, stderr = client.exec_command("ps -ef | grep next")
        print(stdout.read().decode())

        # 3. Check disk and file descriptors
        print("\n--- System health ---")
        stdin, stdout, stderr = client.exec_command("ulimit -n && lsof | wc -l")
        print(f"FD info: {stdout.read().decode()}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run()
