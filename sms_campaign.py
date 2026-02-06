import os
import subprocess
import shlex
import time
import csv
import shlex
from dotenv import load_dotenv

PHONE_IP = "WIFI_NET_PHONE_IP"
PHONE_USER = "USER_ID_TERMUX"
PHONE_PORT = 8022
MESSAGE_TEMPLATE = """Bonjour camarade {} {}, 
Ceci est un message de test pour la campagne SMS.
Cordialement,
Trotsky
"""

def run_ssh(command: str):
    """
    Runs a remote command on the phone via SSH.
    If TERMUX_SSH_PASSWORD is set, uses sshpass to provide the password non-interactively.
    """
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        print("Warning: .env file not found. TERMUX password must be set in environment variable TERMUX_SSH_PASSWORD if needed.")

    password = os.getenv("TERMUX_SSH_PASSWORD")

    # Base ssh options: disable interactive prompts so it won't hang
    ssh_opts = [
        "-p", str(PHONE_PORT),
        "-o", "StrictHostKeyChecking=accept-new",  # first time auto-accept host key
        "-o", "BatchMode=no",                      # allow password auth
        "-o", "ConnectTimeout=10",
    ]

    target = f"{PHONE_USER}@{PHONE_IP}"

    if password:
        # sshpass mode
        cmd = [
            "sshpass", "-e",  # reads password from SSHPASS env var
            "ssh", *ssh_opts,
            target,
            command
        ]
        env = os.environ.copy()
        env["SSHPASS"] = password
        return subprocess.run(cmd, capture_output=True, text=True, env=env)
    else:
        # normal ssh (will prompt for password in terminal)
        cmd = ["ssh", *ssh_opts, target, command]
        return subprocess.run(cmd, capture_output=True, text=True)


def send_sms(to: str, message: str, delay_s: float = 2.0):
    # call the helper script on the phone
    cmd = f"~/send_sms.sh {shlex.quote(to)} {shlex.quote(message)}"
    res = run_ssh(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"SSH failed: {res.stderr.strip()}")
    time.sleep(delay_s)

# Example: load recipients from a CSV: number,message
def send_from_csv(path="contacts.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            name = row["NAME"].strip()
            surname = row["SURNAME"].strip()
            to = row["NUMBER"].strip()
            msg = MESSAGE_TEMPLATE.format(name, surname)
            print(f"Sending to {name} {surname} at {to}...")
            send_sms(to, msg, delay_s=3)
            print("Sent.")

if __name__ == "__main__":
    send_from_csv()
