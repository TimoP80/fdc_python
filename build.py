#!/usr/bin/env python3
"""
Nuitka Build System for Fallout Dialogue Creator
Builds a Python application into a standalone executable.

Usage:
    python build.py                    # Build with default settings
    python build.py --clean            # Clean build artifacts first
    python build.py --debug            # Build with debug symbols
    python build.py --onefile          # Build as single executable
    python build.py --directory dist   # Specify output directory
    python build.py --target linux     # Target specific platform
    python build.py --help             # Show all options
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional


# Default configuration path
DEFAULT_CONFIG = "build_config.json"


class BuildError(Exception):
    """Custom exception for build errors."""
    pass


class NuitkaBuilder:
    """Main class for building the application with Nuitka."""
    
    def __init__(self, config_path: str = DEFAULT_CONFIG):
        """Initialize the builder with configuration."""
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.platform = platform.system()
        self.target_platform = self.platform
        
        # Load configuration
        self._load_config()
        
    def _load_config(self) -> None:
        """Load build configuration from JSON file."""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            # Use default config if file doesn't exist
            self.config = self._get_default_config()
            return
            
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "application": {
                "name": "Fallout Dialogue Creator",
                "version": "2.3.0",
                "main_entry": "main.py"
            },
            "build": {
                "output_dir": "dist",
                "onefile": True,
                "standalone": True
            },
            "compilation": {
                "optimization_level": 3,
                "show_progress": True,
                "assume_yes_for_questions": True
            },
            "hidden_imports": [
                "PyQt6",
                "PyQt6.QtCore", 
                "PyQt6.QtGui",
                "PyQt6.QtWidgets"
            ],
            "data_files": {
                "include": []
            }
        }
    
    def _get_app_name(self) -> str:
        """Get application name from config."""
        return self.config.get("application", {}).get("name", "app")
    
    def _get_output_dir(self) -> str:
        """Get output directory from config."""
        return self.config.get("build", {}).get("output_dir", "dist")
    
    def _get_main_entry(self) -> str:
        """Get main entry point from config."""
        return self.config.get("application", {}).get("main_entry", "main.py")
    
    def clean(self) -> None:
        """Remove all build artifacts."""
        output_dir = self._get_output_dir()
        app_name = self._get_app_name()
        
        print(f"[CLEAN] Cleaning build artifacts...")
        
        # Remove output directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print(f"[CLEAN] Removed: {output_dir}")
        
        # Remove . Nuitka cache directories
        for cache_dir in [".nuitka", "__pycache__"]:
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                print(f"[CLEAN] Removed: {cache_dir}")
        
        # Remove .build directory (Nuitka creates this)
        if os.path.exists(".build"):
            shutil.rmtree(".build")
            print(f"[CLEAN] Removed: .build")
        
        # Remove compiled Python files
        for root, dirs, files in os.walk("."):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') 
                      and d not in ('dist', 'build', 'node_modules', '__pycache__')]
            for file in files:
                if file.endswith('.pyc') or file.endswith('.pyo'):
                    filepath = os.path.join(root, file)
                    os.remove(filepath)
                    print(f"[CLEAN] Removed: {filepath}")
        
        print("[CLEAN] Clean complete!")
    
    def _get_platform_config(self) -> Dict[str, Any]:
        """Get platform-specific configuration."""
        platform_key = self.target_platform.lower()
        return self.config.get(platform_key, {})
    
    def _build_nuitka_args(self, args: argparse.Namespace) -> List[str]:
        """Build the Nuitka command line arguments."""
        nuitka_args: List[str] = []
        
        # Main entry point
        nuitka_args.append(self._get_main_entry())
        
        # Build options
        build_config = self.config.get("build", {})
        compilation_config = self.config.get("compilation", {})
        
        # Output directory
        output_dir = args.directory if args.directory else self._get_output_dir()
        nuitka_args.append(f"--output-dir={output_dir}")
        
        # Onefile mode
        if args.onefile or build_config.get("onefile", True):
            nuitka_args.append("--onefile")
        
        # Standalone mode
        if args.standalone or build_config.get("standalone", True):
            nuitka_args.append("--standalone")
        
        # Show progress bar
        if compilation_config.get("show_progress", True):
            nuitka_args.append("--progress-bar=auto")
        
        # Verbose
        if args.verbose or compilation_config.get("verbose", False):
            nuitka_args.append("--verbose")
        
        # (assume-yes-for-questions removed in newer Nuitka)
        
        # Remove output (disabled due to cleanup issues on Windows)
        # if compilation_config.get("remove_output", True):
        #     nuitka_args.append("--remove-output")
        
        # Follow imports
        if compilation_config.get("follow_imports", True):
            nuitka_args.append("--follow-imports")
        
        # Disable dependency cache to avoid dependency walker download
        nuitka_args.append("--disable-cache=all")
        
        # LTO
        lto = compilation_config.get("lto", "auto")
        if lto and lto != "auto":
            nuitka_args.append(f"--lto={lto}")
        
        # Python optimization level
        opt_level = compilation_config.get("optimization_level", 3)
        if opt_level >= 2:
            nuitka_args.append("--python-flag=-O")
        if opt_level >= 3:
            nuitka_args.append("--python-flag=-OO")
        
        # (c-language option removed in newer Nuitka versions)
        
        # Debug options
        debug_config = self.config.get("debug", {})
        if args.debug or debug_config.get("generate_debug_symbols", False):
            nuitka_args.append("--debug")
            nuitka_args.append("--debugger")
        
        if args.profile or debug_config.get("profile", False):
            nuitka_args.append("--profile")
        
        if debug_config.get("trace_execution", False):
            nuitka_args.append("--trace-execution")
        
        # Plugin configuration
        plugin_config = build_config.get("plugin_enabled", True)
        plugin_name = build_config.get("plugin_name", "pyqt6")
        
        if plugin_config:
            nuitka_args.append(f"--enable-plugin={plugin_name}")
            
            # Include Qt plugins
            qt_plugins = compilation_config.get("include_qt_plugins", [])
            for plugin in qt_plugins:
                nuitka_args.append(f"--include-qt-plugins={plugin}")
        
        # Hidden imports
        hidden_imports = compilation_config.get("hidden_imports", [])
        for imp in hidden_imports:
            nuitka_args.append(f"--include-module={imp}")
        
        # Data files
        data_files_config = self.config.get("data_files", {}).get("include", [])
        for data_file in data_files_config:
            source = data_file.get("source")
            destination = data_file.get("destination", "")
            files = data_file.get("files", [])
            if source:
                # If we have specific files to include
                if files:
                    for file in files:
                        if destination:
                            nuitka_args.append(f"--include-data-files={source}/{file}={destination}/{file}")
                        else:
                            nuitka_args.append(f"--include-data-files={source}/{file}")
                elif destination:
                    nuitka_args.append(f"--include-data-dir={source}={destination}")
                else:
                    nuitka_args.append(f"--include-data-dir={source}")
        
        # Platform-specific options
        platform_config = self._get_platform_config()
        
        if self.target_platform == "Windows":
            icon = platform_config.get("icon")
            if icon and os.path.exists(icon):
                nuitka_args.append(f"--windows-icon-from-ico={icon}")
            
            console = platform_config.get("console", False)
            if console:
                nuitka_args.append("--windows-console-mode=force")
            else:
                nuitka_args.append("--windows-console-mode=disable")
            
            # File version info (deprecated in newer Nuitka, using product-info instead)
            product_name = platform_config.get("product_name", "")
            if product_name:
                nuitka_args.append(f"--product-name={product_name}")
            
            company_name = platform_config.get("company_name", "")
            if company_name:
                nuitka_args.append(f"--company-name={company_name}")
            
            file_version = platform_config.get("file_version", "")
            if file_version:
                nuitka_args.append(f"--file-version={file_version}")
            
            copyright_str = platform_config.get("copyright", "")
            if copyright_str:
                nuitka_args.append(f"--copyright={copyright_str}")
        
        elif self.target_platform == "Linux":
            icon = platform_config.get("icon")
            if icon and os.path.exists(icon):
                nuitka_args.append(f"--linux-icon={icon}")
            
            gcc_options = platform_config.get("gcc_options", [])
            for opt in gcc_options:
                nuitka_args.append(f"--gcc-options={opt}")
        
        elif self.target_platform == "Darwin":  # macOS
            icon = platform_config.get("icon")
            if icon and os.path.exists(icon):
                nuitka_args.append(f"--macos-icon={icon}")
            
            min_version = platform_config.get("macos_min_version", "10.15")
            nuitka_args.append(f"--macos-min-version={min_version}")
            
            product_name = platform_config.get("product_name", "")
            if product_name:
                nuitka_args.append(f"--macos-product-name={product_name}")
        
        # Custom paths
        paths_config = self.config.get("paths", {})
        
        if paths_config.get("python_include"):
            nuitka_args.append(f"--pythonInclude={paths_config['python_include']}")
        
        if paths_config.get("python_library"):
            nuitka_args.append(f"--pythonLibrary={paths_config['python_library']}")
        
        if paths_config.get("cmake_path"):
            nuitka_args.append(f"--cmake={paths_config['cmake_path']}")
        
        if paths_config.get("msvc_version"):
            nuitka_args.append(f"--msvc={paths_config['msvc_version']}")
        
        if paths_config.get("mingw64_dir"):
            nuitka_args.append(f"--mingw64={paths_config['mingw64_dir']}")
        
        return nuitka_args
    
    def build(self, args: argparse.Namespace) -> bool:
        """Run the Nuitka build process."""
        print("=" * 60)
        print(f"Building {self._get_app_name()} with Nuitka")
        print(f"Platform: {self.target_platform}")
        print("=" * 60)
        
        # Verify main entry exists
        main_entry = self._get_main_entry()
        if not os.path.exists(main_entry):
            raise BuildError(f"Main entry point not found: {main_entry}")
        
        # Clean if requested
        if args.clean:
            self.clean()
        
        # Build Nuitka arguments
        nuitka_args = ["python", "-m", "nuitka"] + self._build_nuitka_args(args)
        
        print(f"\n[BUILD] Running: {' '.join(nuitka_args)}\n")
        
        # Run Nuitka
        try:
            result = subprocess.run(
                nuitka_args,
                check=True,
                capture_output=False,
                text=True
            )
            
            # Verify output
            if self._verify_build(args):
                print("\n" + "=" * 60)
                print("[BUILD SUCCESS] Executable created successfully!")
                print("=" * 60)
                return True
            else:
                raise BuildError("Build verification failed")
                
        except subprocess.CalledProcessError as e:
            print(f"\n[BUILD ERROR] Nuitka compilation failed with code: {e.returncode}")
            return False
        except FileNotFoundError:
            print("\n[ERROR] Nuitka is not installed.")
            print("Install it with: pip install nuitka")
            return False
    
    def _verify_build(self, args: argparse.Namespace) -> bool:
        """Verify that the build produced the expected executable."""
        output_dir = args.directory if args.directory else self._get_output_dir()
        app_name = self._get_app_name()
        
        # Determine expected executable name
        if self.target_platform == "Windows":
            exe_name = f"{app_name}.exe"
        else:
            exe_name = app_name
        
        # Check for executable
        exe_path = os.path.join(output_dir, exe_name)
        
        if os.path.exists(exe_path):
            print(f"\n[VERIFY] Found executable: {exe_path}")
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"[VERIFY] Size: {size_mb:.2f} MB")
            return True
        
        # Check for onefile output
        if self.config.get("build", {}).get("onefile", True):
            # Onefile might have different naming
            for file in os.listdir(output_dir):
                if file.endswith(".exe") or file.startswith(app_name):
                    full_path = os.path.join(output_dir, file)
                    if os.path.isfile(full_path):
                        print(f"\n[VERIFY] Found executable: {full_path}")
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        print(f"[VERIFY] Size: {size_mb:.2f} MB")
                        return True
        
        print(f"\n[VERIFY] Could not find expected executable")
        return False


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Nuitka Build System for Fallout Dialogue Creator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py                    Build with default settings
  python build.py --clean            Clean before building
  python build.py --debug            Include debug symbols
  python build.py --onefile          Build as single executable
  python build.py --target linux     Target Linux platform
  python build.py --profile          Enable profiling
  python build.py --verbose          Verbose output

For more information, see BUILD.md
        """
    )
    
    parser.add_argument(
        "--config", 
        default=DEFAULT_CONFIG,
        help="Path to build configuration file (default: build_config.json)"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Build as single executable file"
    )
    
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Build as standalone distribution"
    )
    
    parser.add_argument(
        "--directory", "-d",
        help="Output directory for built files"
    )
    
    parser.add_argument(
        "--target",
        choices=["windows", "linux", "darwin", "macos"],
        help="Target platform (default: current platform)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Include debug symbols"
    )
    
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable profiling support"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()
    
    # Create builder
    try:
        builder = NuitkaBuilder(args.config)
        
        # Set target platform
        if args.target:
            target_map = {
                "windows": "Windows",
                "linux": "Linux", 
                "darwin": "Darwin",
                "macos": "Darwin"
            }
            builder.target_platform = target_map[args.target]
        
        # Run build
        success = builder.build(args)
        
        return 0 if success else 1
        
    except BuildError as e:
        print(f"\n[ERROR] {e}")
        return 1
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
