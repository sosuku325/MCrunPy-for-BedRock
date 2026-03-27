import os
import subprocess
import sys
import threading

SERVER_DIR = "/home/container"
SERVER_EXEC = "./bedrock_server"
os.chdir(SERVER_DIR)
env = os.environ.copy()
env["LD_LIBRARY_PATH"] = SERVER_DIR
print("サーバーを起動しています...")
process = subprocess.Popen(
    [SERVER_EXEC],
    env=env,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,  
    bufsize=1    
)
def read_output(proc):
    for line in iter(proc.stdout.readline, ''):
        if line:
            print(f"[サーバーログ] {line}", end='')
    proc.stdout.close()
output_thread = threading.Thread(target=read_output, args=(process,), daemon=True)
output_thread.start()
try:
    while process.poll() is None:
        user_input = sys.stdin.readline()
        if not user_input:
            break
        process.stdin.write(user_input)
        process.stdin.flush()
except KeyboardInterrupt:
    print("\n強制終了がリクエストされました。サーバーを停止します...")
    process.terminate()
process.wait()
print(f"サーバーが終了しました。(終了コード: {process.returncode})")
