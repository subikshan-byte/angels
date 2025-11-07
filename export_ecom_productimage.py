import os
import datetime

# --- MySQL Credentials ---
USER = "root"
PASSWORD = "Subi14082006@"
DATABASE = "angles"

# --- Backup file name with timestamp ---
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"/root/backups/{DATABASE}_backup_{timestamp}.sql"

# --- Create folder if not exists ---
os.makedirs(os.path.dirname(backup_file), exist_ok=True)

# --- Command to run mysqldump ---
command = f"mysqldump -u {USER} -p'{PASSWORD}' {DATABASE} > {backup_file}"

# --- Execute backup ---
os.system(command)

print(f"✅ Backup created: {backup_file}")


