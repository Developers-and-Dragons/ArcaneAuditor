"""
PyInstaller runtime hook for macOS code signing compatibility.

This hook solves the problem where Apple's codesign requires non-Mach-O files
and directories with periods to be moved from Contents/Frameworks/ to 
Contents/Resources/lib/, but PyInstaller's sys.path doesn't include that location.

This runs BEFORE your application code, during PyInstaller's bootloader phase,
ensuring Python can find all modules regardless of where they physically reside.
"""
import sys
import os

if sys.platform == 'darwin' and hasattr(sys, '_MEIPASS'):
    # PyInstaller sets _MEIPASS to the extraction directory
    # For .app bundles: /Applications/YourApp.app/Contents/MacOS
    
    # Navigate to Contents/ directory
    bundle_macos = sys._MEIPASS
    bundle_contents = os.path.dirname(bundle_macos)
    resources_lib = os.path.join(bundle_contents, 'Resources', 'lib')
    
    if os.path.isdir(resources_lib):
        # Add Resources/lib to the FRONT of sys.path
        # This ensures relocated modules are found first
        if resources_lib not in sys.path:
            sys.path.insert(0, resources_lib)
        
        # Also add any python3.x subdirectories (e.g., python3.12)
        # These contain the Python standard library
        try:
            for item in os.listdir(resources_lib):
                if item.startswith('python3.') and item[7:].replace('.', '').isdigit():
                    py_dir = os.path.join(resources_lib, item)
                    if os.path.isdir(py_dir) and py_dir not in sys.path:
                        sys.path.insert(0, py_dir)
                        
                        # Also add site-packages within this directory
                        site_packages = os.path.join(py_dir, 'site-packages')
                        if os.path.isdir(site_packages) and site_packages not in sys.path:
                            sys.path.insert(0, site_packages)
        except (OSError, IOError):
            # If we can't read the directory, fail silently
            # The app will fail later with clearer import errors if needed
            pass
