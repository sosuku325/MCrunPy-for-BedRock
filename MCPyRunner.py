import os
import subprocess
import sys
import threading
import urllib.request
import json
import tarfile
import stat

SERVER_DIR = "/home/container"
JAVA_DIR = os.path.join(SERVER_DIR, "java_runtime")
PAPER_VERSION = "1.21.11" #好きなバージョンにして
JAR_NAME = "paper.jar"
MEMORY = os.environ.get("SERVER_MEMORY", "1024")
JAVA_URL = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.2%2B13/OpenJDK21U-jdk_x64_linux_hotspot_21.0.2_13.tar.gz"
os.chdir(SERVER_DIR)

def setup_java():
    """Javaのセットアップ"""
    if not os.path.exists(JAVA_DIR):
        print("[システム] Javaが見つかりません。ダウンロード中...")
        archive = "java.tar.gz"
        urllib.request.urlretrieve(JAVA_URL, archive)
        os.makedirs(JAVA_DIR, exist_ok=True)
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(path=JAVA_DIR)
        os.remove(archive)
    
    for root, dirs, files in os.walk(JAVA_DIR):
        if "java" in files and "bin" in root:
            java_path = os.path.join(root, "java")
            st = os.stat(java_path)
            os.chmod(java_path, st.st_mode | stat.S_IEXEC)
            return java_path
    return None
def setup_paper():
    """PaperMCの最新ビルドをダウンロード"""
    if os.path.exists(JAR_NAME):
        return
    print(f"[システム] Paper {PAPER_VERSION} を取得中...")
    try:
        api_url = f"https://api.papermc.io/v2/projects/paper/versions/{PAPER_VERSION}"
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read().decode())
            latest_build = data["builds"][-1]
        
        download_url = f"{api_url}/builds/{latest_build}/downloads/paper-{PAPER_VERSION}-{latest_build}.jar"
        print(f"[システム] ビルド {latest_build} をダウンロード中...")
        urllib.request.urlretrieve(download_url, JAR_NAME)
    except Exception as e:
        print(f"[エラー] Paperのダウンロードに失敗: {e}")
        sys.exit(1)
def accept_eula():
    """eula.txtを作成して同意する"""
    if not os.path.exists("eula.txt"):
        with open("eula.txt", "w") as f:
            f.write("eula=true")
        print("[システム] EULAに同意しました。")
def main():
    java_path = setup_java()
    setup_paper()
    accept_eula()
    if not java_path:
        print("[エラー] Javaの起動パスが見つかりません。")
        return
    cmd = [
        java_path,
        f"-Xmx{MEMORY}M",
        f"-Xms{MEMORY}M",
        "-jar",
        JAR_NAME,
        "nogui"
    ]
    print(f"--- Paperサーバーを起動します (メモリ: {MEMORY}MB) ---")
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    def read_output(proc):
        for line in iter(proc.stdout.readline, ''):
            print(line, end='')
        proc.stdout.close()
    threading.Thread(target=read_output, args=(process,), daemon=True).start()
    try:
        while process.poll() is None:
            user_input = sys.stdin.readline()
            if not user_input:
                break
            process.stdin.write(user_input)
            process.stdin.flush()
    except KeyboardInterrupt:
        process.terminate()
    process.wait()
    print(f"[システム] サーバーが終了しました。")
if __name__ == "__main__":
    main() 
