#!/usr/bin/env python3
"""
SHOPHEATER3000 Setup Verification Script

Checks that all dependencies are installed and source codebases are accessible.
Does NOT require hardware - just verifies software setup.
"""

import sys
import os


def check_packages():
    """Check that all required packages are installed."""
    print("=" * 60)
    print("Checking installed packages...")
    print("=" * 60)
    
    required = {
        'lgpio': '0.2.2.0',
        'click': '8.3.1',
        'w1thermsensor': '2.3.0'
    }
    
    all_ok = True
    
    for package, expected_version in required.items():
        try:
            if package == 'lgpio':
                import lgpio
                version = lgpio.__version__ if hasattr(lgpio, '__version__') else '0.2.2.0'
            elif package == 'click':
                import click
                version = click.__version__
            elif package == 'w1thermsensor':
                import w1thermsensor
                version = w1thermsensor.__version__ if hasattr(w1thermsensor, '__version__') else '2.3.0'
            
            print(f"✓ {package}: {version}")
        except ImportError:
            print(f"✗ {package}: NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_source_paths():
    """Check that all source codebase directories exist."""
    print("\n" + "=" * 60)
    print("Checking source codebase directories...")
    print("=" * 60)
    
    base_dir = os.path.expanduser('~')
    
    required_dirs = {
        'raspi-bts7960': 'Fan control (BTS7960 motor driver)',
        'raspi-ds18b20': 'Temperature sensing (DS18B20)',
        'raspi-flowmeter': 'Flow measurement (FL-408)',
        'raspi-relay-shopheater': 'Valve control (relays)'
    }
    
    all_ok = True
    
    for dirname, description in required_dirs.items():
        path = os.path.join(base_dir, dirname)
        if os.path.isdir(path):
            print(f"✓ {dirname}: {path}")
            print(f"  └─ {description}")
        else:
            print(f"✗ {dirname}: NOT FOUND")
            print(f"  └─ Expected at: {path}")
            all_ok = False
    
    return all_ok


def check_module_imports():
    """Check that all source modules can be imported."""
    print("\n" + "=" * 60)
    print("Checking source module imports...")
    print("=" * 60)
    
    base_dir = os.path.expanduser('~')
    
    modules_to_check = [
        ('raspi-bts7960', 'bts7960_controller', 'BTS7960Controller'),
        ('raspi-ds18b20', 'ds18b20_reader', 'DS18B20Reader'),
        ('raspi-flowmeter', 'flowmeter', 'FlowMeter'),
        ('raspi-relay-shopheater', 'relay_control', 'RelayController')
    ]
    
    all_ok = True
    
    for dirname, module_name, class_name in modules_to_check:
        path = os.path.join(base_dir, dirname)
        
        if path not in sys.path:
            sys.path.append(path)
        
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                print(f"✓ {dirname}/{module_name}.py")
                print(f"  └─ {class_name} class found")
            else:
                print(f"✗ {dirname}/{module_name}.py")
                print(f"  └─ {class_name} class NOT FOUND")
                all_ok = False
        except ImportError as e:
            print(f"✗ {dirname}/{module_name}.py")
            print(f"  └─ Import error: {e}")
            all_ok = False
    
    return all_ok


def check_gpio_permissions():
    """Check if user is in gpio group."""
    print("\n" + "=" * 60)
    print("Checking GPIO permissions...")
    print("=" * 60)
    
    import grp
    import os
    
    try:
        gpio_group = grp.getgrnam('gpio')
        username = os.getenv('USER')
        
        if username in gpio_group.gr_mem:
            print(f"✓ User '{username}' is in 'gpio' group")
            return True
        else:
            print(f"✗ User '{username}' is NOT in 'gpio' group")
            print(f"  Run: sudo usermod -a -G gpio {username}")
            print(f"  Then log out and back in")
            return False
    except KeyError:
        print("✗ 'gpio' group does not exist on this system")
        return False


def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "SHOPHEATER3000 SETUP VERIFICATION" + " " * 10 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    checks = [
        ("Installed Packages", check_packages),
        ("Source Directories", check_source_paths),
        ("Module Imports", check_module_imports),
        ("GPIO Permissions", check_gpio_permissions)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n✗ Error during {check_name}: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for check_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {check_name}")
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! System is ready for integration.")
        print("\nNext steps:")
        print("  1. Test individual modules with hardware")
        print("  2. Create your integration script")
        print("  3. Test SHOPHEATER3000 with all modules together")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Missing packages: pip install -r requirements.txt")
        print("  - Missing directories: Verify source codebase locations")
        print("  - GPIO permissions: sudo usermod -a -G gpio $USER")
    
    print()
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

