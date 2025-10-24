#!/bin/bash
# Deployment Verification Script

echo "═══════════════════════════════════════════════════════"
echo "  RAILWAY DEPLOYMENT - PRE-FLIGHT CHECK"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check required files
echo "📋 Checking Required Files..."
files=("railway.json" "Procfile" ".env.example" "requirements.txt" ".gitignore" "start_api.py")
all_files_present=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (MISSING)"
        all_files_present=false
    fi
done

echo ""
echo "📦 Checking Python Dependencies..."

# Check if key packages are in requirements.txt
required_packages=("fastapi" "uvicorn" "anthropic" "yfinance" "APScheduler" "pytz")
all_packages_present=true

for package in "${required_packages[@]}"; do
    if grep -qi "$package" requirements.txt; then
        echo "  ✓ $package"
    else
        echo "  ✗ $package (MISSING)"
        all_packages_present=false
    fi
done

echo ""
echo "🔐 Checking .gitignore..."

# Check if sensitive files are excluded
sensitive=("config.py" ".env" "api_usage.json" "*_latest.json")
all_excluded=true

for item in "${sensitive}[@]}"; do
    if grep -q "$item" .gitignore; then
        echo "  ✓ $item excluded"
    else
        echo "  ⚠ $item not excluded"
        all_excluded=false
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════"

if [ "$all_files_present" = true ] && [ "$all_packages_present" = true ]; then
    echo "✅ READY FOR DEPLOYMENT!"
    echo ""
    echo "Next steps:"
    echo "  1. git add ."
    echo "  2. git commit -m 'Prepare for Railway deployment'"
    echo "  3. git push origin main"
    echo "  4. Deploy on railway.app"
else
    echo "⚠️  ISSUES FOUND - Fix before deploying"
fi

echo "═══════════════════════════════════════════════════════"
