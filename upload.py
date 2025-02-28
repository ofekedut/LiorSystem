import os
import paramiko
from scp import SCPClient
import zipfile
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------------
# Connection & Project Details
# -------------------------
hostname = "35.159.254.211"  # Change to your target IP/hostname
# hostname = "3.77.245.140"
username = "ubuntu"  # Change as needed
key_file = "/Users/ofekedut/Downloads/OfekMacForMortagesServer.pem"  # Update as needed
# key_file = "/Users/ofekedut/.ssh/perlakey.pem"  # Update as needed

abs_path = os.path.abspath(os.getcwd())
local_directory = os.path.join(abs_path, "server")  # path to your local server directory
zip_file_path = os.path.join(abs_path, "server.zip")

# Base path where code is deployed
remote_base_path = "/home/ubuntu/deployed_projects"
# The directory containing the server code
remote_project_dir = f"{remote_base_path}/server/server"
# Remote path where the zip is uploaded
remote_zip_path = f"{remote_project_dir}/server.zip"
# Virtual environment directory
venv_path = f"{remote_base_path}/server/venv"
# Systemd service name
service_name = "server"


# -------------------------
# Utility Functions
# -------------------------
def zip_directory(directory_path, zip_path):
    """
    Zips up the local directory (excluding __pycache__).
    """
    try:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if '__pycache__' in file or '__pycache__' in root:
                        continue
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, directory_path))
        logging.info(f"Directory {directory_path} zipped successfully at {zip_path}")
        return True
    except Exception as e:
        logging.error(f"Error zipping directory: {e}")
        return False


def upload_file_via_scp(ssh_client, local_file, remote_file):
    """
    Uploads a file to the remote host via SCP.
    """
    try:
        with SCPClient(ssh_client.get_transport()) as scp:
            scp.put(local_file, remote_file)
        logging.info(f"Uploaded {local_file} to {remote_file}")
        return True
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        return False


def exec_command(ssh_client, command):
    """
    Executes a command over SSH and logs stdout/stderr.
    """
    stdin, stdout, stderr = ssh_client.exec_command(command)
    stdout.channel.recv_exit_status()  # Wait for command to finish
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        logging.info(out)
    if err:
        logging.error(err)
    return out, err


# -------------------------
# Main Deployment Function
# -------------------------
def main():
    # 1. Zip the local server directory
    if not zip_directory(local_directory, zip_file_path):
        return  # If zipping fails, abort

    # 2. Initialize SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to remote server
        ssh.connect(hostname=hostname, username=username, key_filename=key_file)
        logging.info("SSH connection established.")

        # 3. Create remote project directories if they don't exist
        exec_command(ssh, f"mkdir -p {remote_project_dir}")

        # 4. Upload the zip file
        if not upload_file_via_scp(ssh, zip_file_path, remote_zip_path):
            return  # If upload fails, abort

        # 5. Extract zip file on remote
        exec_command(ssh, f"unzip -o {remote_zip_path} -d {remote_project_dir}")

        # 6. Remove the zip file after extraction
        exec_command(ssh, f"rm -f {remote_zip_path}")

        # 7. Create virtual environment if needed, then install dependencies
        out, _ = exec_command(ssh, f"test -d {venv_path} && echo 'exists' || echo 'not_exists'")
        if "not_exists" in out:
            logging.info("Creating virtual environment...")
            exec_command(ssh, f"python3 -m venv {venv_path}")

        # Install dependencies
        exec_command(
            ssh,
            f"source {venv_path}/bin/activate && "
            f"pip install --upgrade pip && "
            f"pip install  python-jose python-multipart passlib[bcrypt] asyncio asyncpg fastapi boto3 "
            f"camelot-py opencv-contrib-python opencv-python-headless "
            f"pdf2image PyMuPDF PyPDF2 pytesseract rapidfuzz uvicorn "
            f"'pydantic[email]'"
        )

        # 8. Create or update systemd service
        service_file_path = f"/etc/systemd/system/{service_name}.service"

        # Notice how we set WorkingDirectory to the parent folder
        # and run our file with `-m server.api`.
        service_definition = f"""[Unit]
Description=My Project Service
After=network.target

[Service]
ExecStart={venv_path}/bin/python -m server.api
WorkingDirectory={remote_base_path}/server
Restart=always
User={username}
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH={remote_base_path}/server

[Install]
WantedBy=multi-user.target
"""

        # Check if the service file already exists
        exists_out, _ = exec_command(ssh, f"sudo test -f {service_file_path} && echo 'exists' || echo 'not_exists'")

        # Create or overwrite the service file
        if "not_exists" in exists_out:
            logging.info("Creating systemd service file...")
        else:
            logging.info("Overwriting existing systemd service file...")

        exec_command(ssh, f'echo "{service_definition}" | sudo tee {service_file_path}')

        # Reload systemd daemon & enable the service at startup
        exec_command(ssh, "sudo systemctl daemon-reload")
        exec_command(ssh, f"sudo systemctl enable {service_name}")

        # 9. Restart the service
        exec_command(ssh, f"sudo systemctl restart {service_name}")

        # 10. Display service status
        exec_command(ssh, f"sudo systemctl status {service_name} --no-pager")

        # 11. Clean up local zip file
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
            logging.info(f"Local zip file {zip_file_path} deleted.")

    except Exception as e:
        logging.error(f"Deployment error: {e}")
    finally:
        ssh.close()
        logging.info("SSH connection closed.")


if __name__ == "__main__":
    main()
