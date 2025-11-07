import os
import datetime

# --- MySQL Credentials ---
USER = "root"
PASSWORD = "Subi14082006@"
DATABASE = "angles"

# --- Folder to save backups (change path if needed) ---
backup_dir = "/home/ubuntu/angles"
os.makedirs(backup_dir, exist_ok=True)

# --- File name with timestamp ---
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"{backup_dir}/{DATABASE}_backup_{timestamp}.sql"

# --- Backup command ---
command = f"mysqldump -u {USER} -p'{PASSWORD}' {DATABASE} > {backup_file}"

# --- Run command ---
os.system(command)

print(f"✅ Backup created and saved in: {backup_file}")

