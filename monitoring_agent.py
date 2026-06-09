#!/usr/bin/env python3
"""
Automated Monitoring Agent for GPU Monitor Dashboard
Monitors application logs and system health, reports issues to GitHub
"""

import subprocess
import os
import time
import logging
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
import requests

# Configuration
REPO_OWNER = "wynnep77"
REPO_NAME = "AI-Monitoring-Portal"
LOG_FILE = Path(__file__).parent / "monitoring_agent.log"
DOCKER_LOG_FILE = Path(__file__).parent / "docker_compose.log"
CHECK_INTERVAL = int(os.getenv("MONITOR_CHECK_INTERVAL", "300"))  # Default: 5 minutes
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # Optional: for authenticated requests

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

class MonitoringAgent:
    def __init__(self):
        self.last_log_position = 0
        self.issues_reported = {}  # Track reported issues to avoid duplicates
        self.load_reported_issues()
    
    def load_reported_issues(self):
        """Load previously reported issues from file"""
        issues_file = Path(__file__).parent / "reported_issues.json"
        if issues_file.exists():
            try:
                with open(issues_file, 'r') as f:
                    self.issues_reported = json.load(f)
                logger.info(f"Loaded {len(self.issues_reported)} previously reported issues")
            except Exception as e:
                logger.error(f"Error loading reported issues: {e}")
    
    def save_reported_issues(self):
        """Save reported issues to file"""
        issues_file = Path(__file__).parent / "reported_issues.json"
        try:
            with open(issues_file, 'w') as f:
                json.dump(self.issues_reported, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reported issues: {e}")
    
    def get_docker_logs(self):
        """Get Docker Compose logs"""
        try:
            result = subprocess.run(
                ["docker-compose", "logs", "--tail=100", "backend"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            logger.error("Timeout getting Docker logs")
            return ""
        except Exception as e:
            logger.error(f"Error getting Docker logs: {e}")
            return ""
    
    def detect_errors_in_logs(self, logs):
        """Detect errors and warnings in logs"""
        error_patterns = [
            r"Error:.*",
            r"Exception:.*",
            r"Failed to.*",
            r"Unable to.*",
            r"NVML.*error",
            r"GPU.*not detected",
            r"Connection.*refused",
            r"Port.*already in use",
            r"ModuleNotFoundError",
            r"ImportError",
        ]
        
        errors = []
        for pattern in error_patterns:
            matches = re.findall(pattern, logs, re.IGNORECASE)
            for match in matches:
                errors.append(match)
        
        return errors
    
    def check_gpu_status(self):
        """Check GPU status using nvidia-smi"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"nvidia-smi failed: {result.stderr}"
        except FileNotFoundError:
            return "nvidia-smi not found"
        except Exception as e:
            return f"Error checking GPU: {e}"
    
    def check_container_status(self):
        """Check if containers are running"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error checking containers: {e}"
    
    def create_github_issue(self, title, body, labels=["bug", "monitoring"]):
        """Create a GitHub issue"""
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        data = {
            "title": title,
            "body": body,
            "labels": labels
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            if response.status_code == 201:
                logger.info(f"✅ GitHub issue created: {title}")
                return response.json()
            else:
                logger.error(f"❌ Failed to create GitHub issue: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            return None
    
    def report_issue(self, issue_key, title, body):
        """Report an issue if not already reported"""
        # Check if issue was reported recently (within 24 hours)
        if issue_key in self.issues_reported:
            last_reported = datetime.fromisoformat(self.issues_reported[issue_key])
            if datetime.now() - last_reported < timedelta(hours=24):
                logger.info(f"Issue {issue_key} already reported recently, skipping")
                return
        
        # Create GitHub issue
        issue = self.create_github_issue(title, body)
        if issue:
            self.issues_reported[issue_key] = datetime.now().isoformat()
            self.save_reported_issues()
    
    def monitor(self):
        """Main monitoring loop"""
        logger.info("Starting monitoring agent...")
        
        while True:
            try:
                logger.info("=" * 60)
                logger.info(f"Monitoring check at {datetime.now().isoformat()}")
                
                # Check container status
                container_status = self.check_container_status()
                logger.info(f"Container status:\n{container_status}")
                
                # Check GPU status
                gpu_status = self.check_gpu_status()
                logger.info(f"GPU status: {gpu_status}")
                
                # Get Docker logs
                logs = self.get_docker_logs()
                
                # Detect errors
                errors = self.detect_errors_in_logs(logs)
                if errors:
                    logger.warning(f"Detected {len(errors)} errors in logs")
                    for error in errors[:5]:  # Limit to first 5 errors
                        logger.warning(f"  - {error}")
                    
                    # Report errors to GitHub
                    error_summary = "\n".join(errors[:10])
                    body = f"""
**Automated Monitoring Alert**

**Time:** {datetime.now().isoformat()}
**Errors detected:** {len(errors)}

**Error Summary:**
```
{error_summary}
```

**Container Status:**
```
{container_status}
```

**GPU Status:**
```
{gpu_status}
```

**Recent Logs:**
```
{logs[-1000:]}
```
"""
                    self.report_issue(
                        f"Monitoring Alert: {len(errors)} errors detected",
                        f"Automated monitoring detected {len(errors)} errors in the application logs.",
                        body
                    )
                else:
                    logger.info("✅ No errors detected in logs")
                
                # Check if containers are running
                if "Exit" in container_status or "exited" in container_status.lower():
                    body = f"""
**Container Failure Alert**

**Time:** {datetime.now().isoformat()}

**Container Status:**
```
{container_status}
```

**GPU Status:**
```
{gpu_status}
```
"""
                    self.report_issue(
                        "Monitoring Alert: Container failure detected",
                        "One or more containers have exited or failed to start.",
                        body
                    )
                
                # Check GPU availability
                if "nvidia-smi failed" in gpu_status or "nvidia-smi not found" in gpu_status:
                    body = f"""
**GPU Monitoring Failure Alert**

**Time:** {datetime.now().isoformat()}

**GPU Status:**
```
{gpu_status}
```

**Container Status:**
```
{container_status}
```
"""
                    self.report_issue(
                        "Monitoring Alert: GPU monitoring failure",
                        "Unable to access GPU via nvidia-smi. GPU monitoring may not be working.",
                        body
                    )
                
                logger.info("Monitoring check complete")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait for next check
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("GPU Monitor Dashboard - Automated Monitoring Agent")
    logger.info("=" * 60)
    logger.info(f"Repository: {REPO_OWNER}/{REPO_NAME}")
    logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 60)
    
    agent = MonitoringAgent()
    agent.monitor()
