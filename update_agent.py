#!/usr/bin/env python3
"""
Auto-Update Agent for GPU Monitor Dashboard
Checks for updates from GitHub and applies them automatically
"""

import subprocess
import os
import time
import logging
from datetime import datetime
from pathlib import Path

# Configuration
REPO_URL = "https://github.com/wynnep77/AI-Monitoring-Portal.git"
REPO_DIR = Path(__file__).parent.absolute()
CHECK_INTERVAL = int(os.getenv("UPDATE_CHECK_INTERVAL", "3600"))  # Default: 1 hour
LOG_FILE = REPO_DIR / "update_agent.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {cmd}")
        return -1, "", "Command timed out"
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return -1, "", str(e)

def check_for_updates():
    """Check if there are updates available on GitHub"""
    logger.info("Checking for updates...")
    
    # Fetch latest changes
    returncode, stdout, stderr = run_command("git fetch origin", cwd=REPO_DIR)
    if returncode != 0:
        logger.error(f"Failed to fetch updates: {stderr}")
        return False
    
    # Check if local is behind remote
    returncode, stdout, stderr = run_command("git rev-parse HEAD", cwd=REPO_DIR)
    if returncode != 0:
        logger.error(f"Failed to get current commit: {stderr}")
        return False
    
    local_commit = stdout.strip()
    
    returncode, stdout, stderr = run_command("git rev-parse origin/main", cwd=REPO_DIR)
    if returncode != 0:
        logger.error(f"Failed to get remote commit: {stderr}")
        return False
    
    remote_commit = stdout.strip()
    
    if local_commit != remote_commit:
        logger.info(f"Updates available: {local_commit} -> {remote_commit}")
        return True
    else:
        logger.info("Already up to date")
        return False

def apply_updates():
    """Apply updates from GitHub"""
    logger.info("Applying updates...")
    
    # Pull latest changes
    returncode, stdout, stderr = run_command("git pull origin main", cwd=REPO_DIR)
    if returncode != 0:
        logger.error(f"Failed to pull updates: {stderr}")
        return False
    
    logger.info("Successfully pulled updates")
    return True

def restart_application():
    """Restart the application using Docker Compose"""
    logger.info("Restarting application...")
    
    # Stop the container
    returncode, stdout, stderr = run_command("docker-compose down", cwd=REPO_DIR)
    if returncode != 0:
        logger.error(f"Failed to stop container: {stderr}")
        return False
    
    # Rebuild and start
    returncode, stdout, stderr = run_command("docker-compose up -d --build", cwd=REPO_DIR)
    if returncode != 0:
        logger.error(f"Failed to start container: {stderr}")
        return False
    
    logger.info("Application restarted successfully")
    return True

def update_loop():
    """Main update loop"""
    logger.info(f"Update agent started. Checking every {CHECK_INTERVAL} seconds")
    
    while True:
        try:
            if check_for_updates():
                logger.info("Updates detected, applying...")
                if apply_updates():
                    logger.info("Updates applied successfully, restarting application...")
                    if restart_application():
                        logger.info("Update cycle completed successfully")
                    else:
                        logger.error("Failed to restart application after update")
                else:
                    logger.error("Failed to apply updates")
            
            # Wait for next check
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Update agent stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in update loop: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("GPU Monitor Dashboard Auto-Update Agent")
    logger.info("=" * 60)
    logger.info(f"Repository: {REPO_URL}")
    logger.info(f"Working directory: {REPO_DIR}")
    logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 60)
    
    update_loop()
