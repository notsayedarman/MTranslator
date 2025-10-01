import subprocess
import sys

# ---- List of required packages ----
packages = [
    "selenium",
    "webdriver-manager",
    "Pillow"
]

# ---- Function to install packages ----
def install_package(pkg):
    print(f"Installing {pkg}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# ---- Install all missing packages ----
for pkg in packages:
    try:
        __import__(pkg.split("-")[0])
    except ImportError:
        install_package(pkg)

print("\nAll dependencies installed successfully!")

# ---- Run your main script ----
script_name = "main.py"  # Replace with your actual script filename
print(f"\nRunning {script_name}...\n")
subprocess.run([sys.executable, script_name])
