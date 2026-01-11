#!/bin/bash

# ADMIN IDLI BOOK Workspace Installation Script
# This script installs and activates the custom workspace

echo "=================================="
echo "ADMIN IDLI BOOK Workspace Installer"
echo "=================================="
echo ""

# Get site name
read -p "Enter your site name (default: site1.local): " SITE_NAME
SITE_NAME=${SITE_NAME:-site1.local}

echo ""
echo "📦 Installing workspace for site: $SITE_NAME"
echo ""

# Navigate to bench directory
cd /home/tebi1/frappe-v15/frappe-bench || exit 1

echo "✅ Step 1: Running migrate..."
bench --site "$SITE_NAME" migrate
if [ $? -ne 0 ]; then
    echo "❌ Migration failed!"
    exit 1
fi

echo ""
echo "✅ Step 2: Building assets..."
bench build --app idli_book
if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "✅ Step 3: Clearing cache..."
bench --site "$SITE_NAME" clear-cache

echo ""
echo "✅ Step 4: Restarting bench..."
bench restart

echo ""
echo "=================================="
echo "✅ Installation Complete!"
echo "=================================="
echo ""
echo "📋 Next Steps:"
echo "1. Open your browser and hard refresh (Ctrl + Shift + R)"
echo "2. Click the Workspace Switcher (top-left)"
echo "3. Select 'ADMIN IDLI BOOK'"
echo "4. You should see the sidebar with:"
echo "   - Dashboard"
echo "   - Item"
echo "   - Sales (Estimate, Sales Order, Sales Invoice, Customer)"
echo "   - Purchase (Vendor, Purchase Order, Purchase Bill)"
echo "   - Payment (Receive, Pay)"
echo "   - Reports"
echo ""
echo "📖 For detailed documentation, see:"
echo "   apps/idli_book/WORKSPACE_IMPLEMENTATION.md"
echo ""
