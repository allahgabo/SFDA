#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Render Build Script — SFDA Travel Intelligence
# Runs once before the app starts.
# ─────────────────────────────────────────────────────────────────────────────
set -e  # Exit on any error

echo "══════════════════════════════════════════════"
echo "  SFDA Build — Step 1: System dependencies"
echo "══════════════════════════════════════════════"
# WeasyPrint requires these system packages for PDF generation
apt-get update -qq
apt-get install -y -qq \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu \
    libharfbuzz0b \
    libfontconfig1

echo "══════════════════════════════════════════════"
echo "  SFDA Build — Step 2: React frontend"
echo "══════════════════════════════════════════════"
cd frontend
npm install --silent
npm run build
echo "✅ React build complete"

echo "══════════════════════════════════════════════"
echo "  SFDA Build — Step 3: Copy build to Django"
echo "══════════════════════════════════════════════"
cd ..
# Copy React build into backend so Django can serve it
rm -rf backend/frontend_build
cp -r frontend/build backend/frontend_build
echo "✅ React build copied to backend/frontend_build"

echo "══════════════════════════════════════════════"
echo "  SFDA Build — Step 4: Python dependencies"
echo "══════════════════════════════════════════════"
cd backend
pip install -r requirements.txt --quiet
echo "✅ Python packages installed"

echo "══════════════════════════════════════════════"
echo "  SFDA Build — Step 5: Django setup"
echo "══════════════════════════════════════════════"
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py create_default_user
echo "✅ Static files collected, migrations applied"

echo ""
echo "✅ Build complete!"
