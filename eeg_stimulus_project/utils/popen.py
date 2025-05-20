import subprocess

try:
    subprocess.Popen(["cmd.exe", "/C", "start", "cmd.exe", "/K", "C:\\Vision\\LabRecorder\\LabRecorder.exe"])
    print("LabRecorder started.")
except Exception as e:
    print(f"Failed to start LabRecorder: {e}")

try:
    subprocess.Popen(["C:\\Vision\\actiCHamp-1.15.1-win32\\actiCHamp.exe"])
    print("actiCHamp started.")
except Exception as e:
    print(f"Failed to start actiCHamp: {e}")