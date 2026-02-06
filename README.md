# Android Termux SMS Automation

## Introduction
Use your Android phone (with an active SIM plan) as a remote SMS gateway while you coordinate campaigns from your computer. This project leverages Termux, SSH, and Python automation so the PC queues messages and the phone sends them via its native SMS capabilities.

## Project Overview
- The phone runs Termux + Termux:API to expose `termux-sms-send` and an OpenSSH server.
- The PC loads recipients from `contacts.csv`, connects over SSH, and executes `~/send_sms.sh` for each row.
- Credentials are supplied via `.env` or environment variables, and automation is paced to respect carrier policies.

## Requirements
- Android mobile phone on the same Wi-Fi network as the PC (Termux + Termux:API installed and granted SMS permission).
- PC with [uv](https://github.com/astral-sh/uv), Python 3.10+, and `sshpass` installed (`sudo apt-get install sshpass`, `brew install hudochenkov/sshpass/sshpass`, or use WSL on Windows).
- OpenSSH client on the PC (built-in on Windows/macOS/Linux) and a stable LAN connection.
- Opt-in contact list stored as `contacts.csv` (semicolon-delimited `NOM;PRENOM;NUMERO`).

## Getting Started

### 1. Prepare the Android phone (Termux)
1. Install Termux and Termux:API from the same source (F-Droid recommended); avoid mixing signatures.
2. Initial packages:

   ```bash
   pkg update -y
   pkg upgrade -y
   pkg install -y termux-api openssh python net-tools
   termux-setup-storage
   termux-battery-status
   ```

3. Grant SMS permission: Android Settings → Apps → Termux:API → Permissions → enable SMS. Test with `termux-sms-send -n +1XXXXXXXX "Test"`.
4. Enable SSH access:
   ```bash
   passwd              # sets the Termux user password
   sshd                # default port 8022
   pgrep -a sshd       # confirm server is running
   ```
5. Create the helper script:

   ```bash
   cat <<'EOF' > ~/send_sms.sh
   #!/data/data/com.termux/files/usr/bin/bash
   TO="$1"
   MSG="$2"
   if [ -z "$TO" ] || [ -z "$MSG" ]; then
     echo "Usage: send_sms.sh <number> <message>"
     exit 1
   fi
   termux-sms-send -n "$TO" "$MSG"
   echo "OK"
   EOF
   chmod +x ~/send_sms.sh
   ~/send_sms.sh +1XXXXXXXX "Hello from Termux"
   ```

6. Battery/background tweaks: Settings → Apps → Termux / Termux:API → Battery → Unrestricted (prevents Android from killing `sshd`).

#### 1.1 Get Phone's user and IP
1. execute `whoami` in Termux. Write down your TERMUX_USER, e.g. `u0_1234`
2. Obtain the phone's IP within your WiFi network. Call `ifconfig` in the Termux terminal.  The IP address should be something like `inet 192.168.1.X` -> `PHONE_IP`
3. Netlink limitations: if `ip`/`ss` fails, retrieve the phone IP from Android Wi-Fi details, `ifconfig` (from `net-tools`), or `getprop dhcp.wlan0.ipaddress`.

### 2. Prepare the PC
1. Confirm SSH client availability: `ssh -V`.
2. Install `sshpass` (needed for non-interactive passwords):
   - Ubuntu/Debian: `sudo apt-get install -y sshpass`
   - macOS (Homebrew): `brew install hudochenkov/sshpass/sshpass`
   - Windows: run the Python script inside WSL or use another POSIX environment that supports `sshpass`.
3. Copy `.env.example` (or edit `.env`) and set `TERMUX_SSH_PASSWORD` to the password you just defined with `passwd` in Termux.
4. Test SSH manually: `ssh -p 8022 <TERMUX_USER>@<PHONE_IP>`.

### 3. Install Python dependencies with uv
1. Install uv if missing (`pip install uv` or download the standalone binary).
2. From the project root:

   ```bash
   uv sync                # creates .venv and installs deps from pyproject/uv.lock
   uv run python --version
   ```

3. Subsequent commands can be run with `uv run ...` or by activating `.venv`.

### 4. Configure environment variables
- `.env` must contain `TERMUX_SSH_PASSWORD=<your_termux_password>` (same value you applied with `passwd`).
- Optionally export `TERMUX_SSH_PASSWORD` in your shell (`export TERMUX_SSH_PASSWORD=...` or `$env:TERMUX_SSH_PASSWORD = "..."`).

## Running a Campaign
1. Populate `contacts.csv` with semicolon-delimited data:

   ```text
   NOM;PRENOM;NUMERO
   Doe;John;+1444333222
   Doe;Jennifer;+1222333444
   ```

2. Adjust `MESSAGE_TEMPLATE` in `sms_campaign.py` if necessary. The default inserts first/last name into a friendly French test message.
3. Start the Termux `sshd` server and ensure the phone stays awake/unrestricted.
4. Launch the campaign from your PC:

   ```bash
   uv run python sms_campaign.py
   ```

5. The script reads each row, logs progress, and spaces messages (default 3 seconds). Monitor the terminal for failures; exceptions include SSH issues or missing permissions.

## Important Notes
- Respect carrier fair-use policies; throttle between 2–5 seconds to avoid spam flags.
- Maintain opt-in records and offer opt-out keywords (e.g., STOP) to remain compliant.
- Keep `sshd` accessible only on the local network—never expose port 8022 to the internet.
- Safeguard `.env` because it stores your Termux password.

## Troubleshooting
- **SSH connection fails**: Ensure `sshd` is active (`pgrep -a sshd`) and confirm phone IP/port 8022. Test locally from the phone: `ssh -p 8022 localhost`.
- **Termux lacks IP tools**: Install `net-tools` and run `ifconfig`, or read Wi-Fi advanced settings.
- **SMS sending blocked**: Revisit Android Settings → Apps → Termux:API → Permissions and grant SMS; test `termux-sms-send` manually.
- **Battery optimizations kill SSH**: Set Termux and Termux:API to Unrestricted battery usage.
- **`sshpass` missing**: Install it via package manager or run inside WSL where it is available.

## Repository Structure
- `sms_campaign.py` – orchestrates SSH calls and CSV parsing.
- `contacts.csv` – sample recipient list (semicolon separated).
- `.env` – stores the Termux SSH password used by `sshpass`.
- `docs/` – supplementary documentation.
- `pyproject.toml`, `uv.lock` – dependency definitions consumed by uv.

## Next Steps
- Expand `MESSAGE_TEMPLATE` with localization or personalization tokens.
- Add delivery logging (e.g., SQLite or CSV append) before scaling higher-volume campaigns.

