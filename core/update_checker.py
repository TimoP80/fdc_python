"""
Update Checker Module for Fallout Dialogue Creator
Handles checking for updates from GitHub releases, downloading updates, and installation.
"""

import logging
import os
import shutil
import hashlib
import urllib.request
import json
import re
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from packaging import version as pkg_version

from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)


# Application version - should match main.py
APP_VERSION = "2.3.0"
GITHUB_REPO = "TimoP80/fdc_python"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"


@dataclass
class UpdateInfo:
    """Information about an available update"""
    current_version: str
    latest_version: str
    release_name: str
    release_notes: str
    download_url: str
    download_size: int  # in bytes
    published_at: str
    asset_name: str  # name of the downloadable asset


class UpdateCheckerSignals(QObject):
    """Signals for update checking operations"""
    check_started = pyqtSignal()
    check_completed = pyqtSignal(bool, str)  # success, message
    update_available = pyqtSignal(UpdateInfo)
    update_not_available = pyqtSignal(str)  # current version message
    download_progress = pyqtSignal(int)  # percentage
    download_completed = pyqtSignal(str)  # path to downloaded file
    download_failed = pyqtSignal(str)  # error message
    install_completed = pyqtSignal(bool, str)  # success, message


class UpdateChecker(QObject):
    """
    Main update checker class that handles all update-related operations.
    Runs on background threads to avoid freezing the UI.
    """
    
    def __init__(self, settings: Optional[Any] = None):
        super().__init__()
        self._settings = settings
        self._current_version = APP_VERSION
        self._signals = UpdateCheckerSignals()
        
    @property
    def signals(self) -> UpdateCheckerSignals:
        return self._signals
    
    @property
    def current_version(self) -> str:
        return self._current_version
    
    def set_settings(self, settings: Any):
        """Set the settings object for storing check timestamps"""
        self._settings = settings
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two semantic version strings.
        Returns: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        try:
            v1_parsed = pkg_version.parse(v1)
            v2_parsed = pkg_version.parse(v2)
            if v1_parsed < v2_parsed:
                return -1
            elif v1_parsed > v2_parsed:
                return 1
            return 0
        except Exception as e:
            logger.error(f"Version comparison error: {e}")
            # Fallback to string comparison
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            return 0
    
    def parse_release_notes(self, body: str) -> str:
        """Parse and clean release notes from GitHub"""
        if not body:
            return "No release notes available."
        # Limit to first 2000 characters to avoid very long descriptions
        notes = body[:2000]
        if len(body) > 2000:
            notes += "\n\n... (truncated)"
        return notes
    
    def check_for_updates(self) -> Tuple[bool, Optional[UpdateInfo], str]:
        """
        Check GitHub for updates.
        Returns: (success, update_info, message)
        """
        logger.info(f"check_for_updates: Starting (thread: {threading.current_thread().name})")
        
        try:
            self._signals.check_started.emit()
            logger.info("check_for_updates: check_started signal emitted")
        except Exception as e:
            logger.exception(f"check_for_updates: Error emitting check_started: {e}")
        
        try:
            logger.info(f"Checking for updates. Current version: {self._current_version}")
            
            # Create SSL context that handles certificates
            import ssl
            ssl_context = ssl.create_default_context()
            
            # Create request with user agent
            request = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    'User-Agent': f'FalloutDialogueCreator/{self._current_version}'
                }
            )
            
            with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
                if response.status != 200:
                    return False, None, f"GitHub API returned status {response.status}"
                
                data = response.read().decode('utf-8')
                releases = json.loads(data)
            
            if not releases or len(releases) == 0:
                return False, None, "No releases found"
            
            # Get the latest release
            latest = releases[0]
            latest_version = latest.get('tag_name', '').lstrip('vV')
            
            # Find a suitable asset to download (prefer .zip or .tar.gz)
            download_url = None
            download_size = 0
            asset_name = ""
            
            for asset in latest.get('assets', []):
                asset_name = asset.get('name', '')
                if asset_name.endswith(('.zip', '.tar.gz', '.exe', '.msi')):
                    download_url = asset.get('browser_download_url')
                    download_size = asset.get('size', 0)
                    break
            
            # If no asset found, try to get source code
            if not download_url:
                download_url = latest.get('zipball_url')
                asset_name = f"source-{latest_version}.zip"
            
            update_info = UpdateInfo(
                current_version=self._current_version,
                latest_version=latest_version,
                release_name=latest.get('name', f'v{latest_version}'),
                release_notes=self.parse_release_notes(latest.get('body', '')),
                download_url=download_url,
                download_size=download_size,
                published_at=latest.get('published_at', ''),
                asset_name=asset_name
            )
            
            # Compare versions
            cmp_result = self.compare_versions(self._current_version, latest_version)
            
            if cmp_result < 0:  # Update available
                logger.info(f"Update available: {latest_version} > {self._current_version}")
                self._signals.update_available.emit(update_info)
                return True, update_info, f"Update {latest_version} is available"
            else:
                msg = f"You are running the latest version ({self._current_version})"
                logger.info(msg)
                self._signals.update_not_available.emit(msg)
                return True, None, msg
                
        except urllib.error.URLError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            self._signals.check_completed.emit(False, error_msg)
            return False, None, error_msg
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse GitHub response: {str(e)}"
            logger.error(error_msg)
            self._signals.check_completed.emit(False, error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error checking for updates: {str(e)}"
            logger.error(error_msg)
            self._signals.check_completed.emit(False, error_msg)
            return False, None, error_msg
    
    def download_update(self, update_info: UpdateInfo, 
                       download_path: Path) -> Tuple[bool, str]:
        """
        Download the update file.
        Returns: (success, file_path_or_error_message)
        """
        try:
            logger.info(f"Downloading update from {update_info.download_url}")
            
            # Create download directory if needed
            download_path.mkdir(parents=True, exist_ok=True)
            
            output_file = download_path / update_info.asset_name
            
            # Download with progress
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    progress = int((block_num * block_size * 100) / total_size)
                    self._signals.download_progress.emit(min(progress, 100))
            
            urllib.request.urlretrieve(
                update_info.download_url,
                str(output_file),
                reporthook=report_progress
            )
            
            logger.info(f"Download completed: {output_file}")
            self._signals.download_completed.emit(str(output_file))
            return True, str(output_file)
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            logger.error(error_msg)
            self._signals.download_failed.emit(error_msg)
            return False, error_msg
    
    def install_update(self, download_file: Path, 
                      app_path: Path) -> Tuple[bool, str]:
        """
        Install the downloaded update.
        For simplicity, this extracts/replaces files in the app directory.
        Returns: (success, message)
        """
        try:
            logger.info(f"Installing update from {download_file}")
            
            if not download_file.exists():
                return False, "Downloaded file not found"
            
            # Create backup
            backup_dir = app_path / "backup"
            backup_dir.mkdir(exist_ok=True)
            
            # For .zip files, extract and replace
            if download_file.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(download_file, 'r') as zip_ref:
                    # Extract to temp first
                    temp_dir = app_path / "temp_update"
                    temp_dir.mkdir(exist_ok=True)
                    zip_ref.extractall(temp_dir)
                    
                    # Find the extracted folder (usually has the repo name)
                    extracted_items = list(temp_dir.iterdir())
                    if extracted_items:
                        source_dir = extracted_items[0]
                        if source_dir.is_dir():
                            # Replace files in app directory
                            for item in source_dir.iterdir():
                                dest = app_path / item.name
                                if item.is_file():
                                    if dest.exists():
                                        dest.replace(backup_dir / item.name)
                                    item.replace(dest)
                                elif item.is_dir() and item.name not in ['backup', 'temp_update']:
                                    # Handle directories
                                    if dest.exists():
                                        shutil.rmtree(dest)
                                    shutil.copytree(item, dest)
                    
                    # Clean up temp
                    shutil.rmtree(temp_dir)
            
            logger.info("Update installed successfully")
            self._signals.install_completed.emit(True, "Update installed successfully. Please restart the application.")
            return True, "Update installed. Please restart."
            
        except Exception as e:
            error_msg = f"Installation failed: {str(e)}"
            logger.error(error_msg)
            self._signals.install_completed.emit(False, error_msg)
            return False, error_msg


class UpdateCheckWorker(QThread):
    """
    Background worker for checking updates.
    """
    
    def __init__(self, checker: UpdateChecker):
        super().__init__()
        self._checker = checker
        self._error = None
        
    def run(self):
        """Run update check in background"""
        try:
            logger.info("UpdateCheckWorker: Starting update check")
            self._checker.check_for_updates()
            logger.info("UpdateCheckWorker: Update check completed")
        except Exception as e:
            logger.exception(f"UpdateCheckWorker: Error during update check: {e}")
            self._error = e
            # Emit check_completed signal with error
            try:
                self._checker.signals.check_completed.emit(False, str(e))
            except Exception as emit_error:
                logger.error(f"UpdateCheckWorker: Failed to emit error signal: {emit_error}")
        finally:
            # Ensure the thread exits cleanly
            self.quit()

    def __del__(self):
        """Clean up worker"""
        if self.isRunning():
            self.quit()
            self.wait(1000)


class UpdateDownloadWorker(QThread):
    """
    Background worker for downloading updates.
    """
    
    def __init__(self, checker: UpdateChecker, update_info: UpdateInfo, download_path: Path):
        super().__init__()
        self._checker = checker
        self._update_info = update_info
        self._download_path = download_path
        
    def run(self):
        """Run download in background"""
        self._checker.download_update(self._update_info, self._download_path)


class UpdateManager(QObject):
    """
    High-level manager that coordinates update checking, downloading, and installation.
    """
    
    def __init__(self, settings: Optional[Any] = None):
        super().__init__()
        self._checker = UpdateChecker(settings)
        self._settings = settings
        
    @property
    def signals(self) -> UpdateCheckerSignals:
        return self._checker.signals
    
    def check_for_updates(self):
        """Start update check in background"""
        worker = UpdateCheckWorker(self._checker)
        worker.start()
        return worker
    
    def download_update(self, update_info: UpdateInfo, download_path: Path = None):
        """Download update in background"""
        if download_path is None:
            download_path = Path.home() / ".fallout_dialogue_creator" / "updates"
        
        worker = UpdateDownloadWorker(self._checker, update_info, download_path)
        worker.start()
        return worker
    
    def install_update(self, download_file: Path, app_path: Path = None):
        """Install the downloaded update"""
        if app_path is None:
            # Get app path from main.py logic
            import sys
            if getattr(sys, 'frozen', False):
                app_path = Path(sys.executable).parent
            else:
                app_path = Path(__file__).parent.parent
        
        return self._checker.install_update(download_file, app_path)
    
    def save_check_timestamp(self):
        """Save the last check timestamp to settings"""
        if self._settings:
            self._settings.set_value('last_update_check', datetime.now().isoformat())
    
    def get_last_check_time(self) -> Optional[datetime]:
        """Get the last check timestamp from settings"""
        if self._settings:
            try:
                timestamp = self._settings.get_last_update_check()
                if timestamp:
                    try:
                        return datetime.fromisoformat(timestamp)
                    except ValueError:
                        logger.warning(f"Invalid timestamp format: {timestamp}")
            except Exception as e:
                logger.error(f"Error getting last check time: {e}")
        return None
