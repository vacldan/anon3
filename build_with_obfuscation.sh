#!/bin/bash
# Build script with PyArmor obfuscation
# This ensures all Python files are obfuscated before packaging

set -e  # Exit on error

echo "=========================================="
echo "  Building with PyArmor Obfuscation"
echo "=========================================="

# Step 1: Clean old obfuscated files
echo ""
echo "[1/5] Cleaning old obfuscated files..."
rm -rf dist_obfuscated/
mkdir -p dist_obfuscated/

# Step 2: Obfuscate all Python files
echo ""
echo "[2/5] Obfuscating Python files with PyArmor..."

# Obfuscate main scripts
echo "  → Obfuscating main Python scripts..."
pyarmor gen -O dist_obfuscated/ \
  validate_license_standalone.py \
  anonymize_cli.py \
  deanonymizator.py \
  pdf2docx_cli.py

# Obfuscate licensing module
echo "  → Obfuscating licensing module..."
mkdir -p dist_obfuscated/licensing
pyarmor gen -O dist_obfuscated/licensing/ \
  licensing/__init__.py \
  licensing/hw_fingerprint.py \
  licensing/license_validator.py \
  licensing/license_generator.py

# Remove duplicate PyArmor runtime (keep only one in root)
echo "  → Cleaning up duplicate runtimes..."
rm -rf dist_obfuscated/licensing/pyarmor_runtime_*

echo "  ✓ All Python files obfuscated"

# Step 3: Backup original files and replace with obfuscated
echo ""
echo "[3/5] Replacing original files with obfuscated versions..."
mkdir -p .backup_originals/

# Backup and replace main scripts
for file in validate_license_standalone.py anonymize_cli.py deanonymizator.py pdf2docx_cli.py; do
  if [ -f "$file" ]; then
    echo "  → Backing up $file"
    cp "$file" ".backup_originals/$file"
    cp "dist_obfuscated/$file" "$file"
  fi
done

# Backup and replace licensing module
echo "  → Backing up licensing/ module"
cp -r licensing/ .backup_originals/licensing/
cp -r dist_obfuscated/licensing/* licensing/

# Copy PyArmor runtime
echo "  → Copying PyArmor runtime"
cp -r dist_obfuscated/pyarmor_runtime_*/ ./

echo "  ✓ Obfuscated files in place"

# Step 4: Build with electron-builder
echo ""
echo "[4/5] Building Electron app..."
npm run build

# Step 5: Restore original files
echo ""
echo "[5/5] Restoring original Python files..."

for file in validate_license_standalone.py anonymize_cli.py deanonymizator.py pdf2docx_cli.py; do
  if [ -f ".backup_originals/$file" ]; then
    cp ".backup_originals/$file" "$file"
  fi
done

cp -r .backup_originals/licensing/* licensing/

# Clean up PyArmor runtime from root (it's now in the packaged app)
rm -rf pyarmor_runtime_*/

echo "  ✓ Original files restored"

echo ""
echo "=========================================="
echo "  ✓ Build Complete!"
echo "=========================================="
echo ""
echo "Installer created in: dist/"
echo "All Python files in the installer are OBFUSCATED."
echo "MASTER_SECRET is protected and not readable."
echo ""
