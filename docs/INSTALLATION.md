# Installation Guide - Idli Book

Complete guide for installing Idli Book from GitHub on a Frappe/ERPNext instance.

---

## Prerequisites

Before installing Idli Book, ensure you have:

1. **Frappe Bench Setup**
   - Frappe Framework v15.x installed
   - A working bench environment
   - Python 3.10 or higher

2. **System Requirements**
   - Ubuntu 20.04 or higher (or compatible Linux distribution)
   - MariaDB 10.3+ or PostgreSQL 12+
   - Node.js 18+ and npm
   - Git installed

3. **Permissions**
   - Access to the bench directory
   - Ability to run bench commands

---

## Installation Steps

### Step 1: Get the App from GitHub

Navigate to your bench directory and fetch the app:

```bash
cd /path/to/frappe-bench
bench get-app https://github.com/YOUR_USERNAME/idli_book.git
```

**To install from a specific branch:**
```bash
bench get-app https://github.com/YOUR_USERNAME/idli_book.git --branch BRANCH_NAME
```

**Examples:**
```bash
# Install from main branch (default)
cd ~/frappe-bench
bench get-app https://github.com/praveeny/idli_book.git

# Install from develop branch
bench get-app https://github.com/praveeny/idli_book.git --branch develop

# Install from a specific version tag
bench get-app https://github.com/praveeny/idli_book.git --branch v1.0.2
```

This will clone the repository into `apps/idli_book`.

---

### Step 2: Install the App on Your Site

```bash
bench --site YOUR_SITE_NAME install-app idli_book
```

**Example:**
```bash
bench --site mysite.local install-app idli_book
```

This will:
- Install all doctypes (29 DocTypes)
- Create database tables
- Set up workspaces (14) and reports (27)
- Register the app with your site

---

### Step 3: Run Database Migration

```bash
bench --site YOUR_SITE_NAME migrate
```

This ensures all database schemas are up to date.

---

### Step 4: Install Python Dependencies

The app requires additional Python libraries:

```bash
cd /path/to/frappe-bench

# For UPI QR Code generation
./env/bin/pip install qrcode[pil]

# For AI Chatbot (optional but recommended)
./env/bin/pip install -U google-generativeai
```

---

### Step 5: Build Assets

```bash
bench build --app idli_book
```

This compiles JavaScript and CSS assets including the chatbot widget.

---

### Step 6: Restart Bench

**For Development:**
```bash
# Stop the current server (Ctrl+C)
bench start
```

**For Production:**
```bash
bench restart
```

---

## Initial Configuration

After installation, configure the following:

### 1. IB Organization Settings

Navigate to: **Search → IB Organization**

Configure:
- Organization Name
- GSTIN (if applicable)
- Address Details
- Financial Year Start/End
- Base Currency (links to IB Currency)

**Accounting Defaults:**
- Default Receivable Account
- Default Payable Account
- Default Income Account
- Default Expense Account
- Default Bank Account

### 2. Chart of Accounts

Review the auto-created Chart of Accounts:
- Navigate to **IB Chart of Accounts** list
- Verify account structure
- Add any custom accounts if needed

### 3. Payment Settings (Optional)

**For UPI QR Code Payments:**

Navigate to: **Search → IB Payment Settings**

1. Check **Enable UPI QR Code**
2. Enter **UPI ID (VPA)** (e.g., `business@okicici`)
3. Enter **Payee Name**
4. Save

**For Razorpay Integration (Optional):**
1. Check **Enable Payment Gateway**
2. Enter **Razorpay Key ID**
3. Enter **Razorpay Key Secret**
4. Save

### 4. AI Chatbot Settings (Optional)

Navigate to: **Search → IB Chatbot Settings**

1. Check **Enable Chatbot**
2. Set **LLM Provider** to "Google Gemini"
3. Leave **Model** field blank (auto-discovery)
4. Enter **API Key** from [Google AI Studio](https://aistudio.google.com/apikey)
5. Save

### 5. Email Settings

Configure SMTP in Frappe for invoice email delivery:

Navigate to: **Settings → Email → Email Account**

Set up your outgoing email account.

---

## Post-Installation Setup

### Create Master Data

1. **States** (for GST):
   - Add states with GST codes
   - Required for tax calculations

2. **Tax Masters**:
   - Create CGST, SGST, IGST tax entries
   - Link to appropriate GL accounts

3. **Customers**:
   - Add your customers
   - Note: Receivable accounts are auto-created

4. **Vendors**:
   - Add your vendors
   - Note: Payable accounts are auto-created

5. **Items**:
   - Add products/services
   - Configure inventory tracking if needed
   - Set tax rates

---

## Verification Steps

### Test the Installation

1. **Create an Estimate**
   - Go to **Idli Book → Sales → New Estimate**
   - Select customer, add items
   - Submit and check for errors
   - Verify email is sent with Accept/Reject links

2. **Create a Sales Invoice**
   - Create from estimate or standalone
   - Submit and verify:
     - GL entries created
     - Stock updated (if tracked)
     - Email sent (if configured)

3. **Check Reports**
   - Open **IB Trial Balance**
   - Open **IB Profit and Loss**
   - Verify data appears correctly

4. **Test UPI Payment Page** (if configured):
   - Create an invoice
   - Check email for "Pay Now" button
   - Click and verify payment page loads
   - Verify QR code displays

5. **Test AI Chatbot** (if configured):
   - Look for purple chat icon in bottom-right
   - Click and type "Show me all customers"
   - Verify response with data

### Verify Installation Summary

```bash
bench --site YOUR_SITE console
```

```python
# Check DocTypes
doctypes = frappe.get_all("DocType", filters={"module": "idli_book"}, pluck="name")
print(f"DocTypes installed: {len(doctypes)}")

# Check Workspaces
workspaces = frappe.get_all("Workspace", filters={"module": "idli_book"}, pluck="name")
print(f"Workspaces installed: {len(workspaces)}")
```

Expected: 29 DocTypes, 14 Workspaces

---

## Common Installation Issues

### Issue 1: "App not found" error
**Solution:**
```bash
# Make sure you're in the bench directory
cd /path/to/frappe-bench

# Check if app exists
ls apps/idli_book

# If not, run get-app again
bench get-app https://github.com/YOUR_USERNAME/idli_book.git
```

### Issue 2: Migration fails
**Solution:**
```bash
# Clear cache and retry
bench --site YOUR_SITE clear-cache
bench --site YOUR_SITE migrate
```

### Issue 3: Payment page shows 404
**Solution:**
```bash
# Build assets and restart
bench build --app idli_book
bench restart

# Clear browser cache
# Ctrl+Shift+Delete in browser
```

### Issue 4: QR code not generating
**Solution:**
```bash
# Install qrcode library
./env/bin/pip install qrcode[pil]

# Restart bench
bench restart
```

### Issue 5: Email sending fails
**Solution:**
- Check customer email is valid (not "Administrator")
- Configure SMTP settings in Frappe
- Check Email Account configuration

### Issue 6: Chatbot not appearing
**Solution:**
```bash
# Install google-generativeai
./env/bin/pip install -U google-generativeai

# Build assets
bench build --app idli_book

# Restart
bench restart
```

### Issue 7: Chatbot returns errors
**Solution:**
- Check API key is valid at [Google AI Studio](https://aistudio.google.com/apikey)
- Leave model field blank for auto-discovery
- Check Error Log for details

---

## Upgrading

To upgrade to a new version:

```bash
# Pull latest changes
cd /path/to/frappe-bench/apps/idli_book
git pull

# Update site
cd /path/to/frappe-bench
bench --site YOUR_SITE migrate

# Build assets
bench build --app idli_book

# Restart
bench restart
```

---

## Uninstallation

To remove the app:

```bash
# Uninstall from site
bench --site YOUR_SITE uninstall-app idli_book

# Remove from bench
bench remove-app idli_book
```

⚠️ **Warning**: This will delete all data associated with the app!

---

## Production Deployment

For production environments:

1. **Enable Production Mode:**
   ```bash
   sudo bench setup production YOUR_USER
   ```

2. **Enable Supervisor:**
   ```bash
   sudo bench setup supervisor
   sudo supervisorctl reload
   ```

3. **Enable Nginx:**
   ```bash
   sudo bench setup nginx
   sudo service nginx reload
   ```

4. **SSL Certificate** (recommended):
   ```bash
   sudo bench setup lets-encrypt YOUR_SITE_NAME
   ```

---

## Quick Start Checklist

### Core Installation
- [ ] Frappe v15 installed
- [ ] Run `bench get-app` command
- [ ] Run `bench install-app` command
- [ ] Run `bench migrate`
- [ ] Install qrcode library: `./env/bin/pip install qrcode[pil]`
- [ ] Build assets: `bench build --app idli_book`
- [ ] Restart bench

### Configuration
- [ ] Configure IB Organization
- [ ] Set up Chart of Accounts
- [ ] Configure Payment Settings (UPI/Razorpay)
- [ ] Set up Email Account (SMTP)
- [ ] Add States for GST
- [ ] Create sample Customer
- [ ] Create sample Item

### AI Chatbot (Optional)
- [ ] Install google-generativeai: `./env/bin/pip install -U google-generativeai`
- [ ] Get API key from Google AI Studio
- [ ] Configure IB Chatbot Settings
- [ ] Enable chatbot
- [ ] Test with sample query

### Verification
- [ ] Test with sample Estimate
- [ ] Test with sample Invoice
- [ ] Verify reports work
- [ ] Verify chatbot works (if enabled)

---

## Support

If you encounter issues:

1. Check the [Complete Documentation](./complete_documentation.md)
2. Review [CHANGELOG](./CHANGELOG.md) for known issues
3. Check GitHub Issues
4. Contact: jaga03038@gmail.com

---

## Additional Resources

- [Frappe Bench Commands](https://frappeframework.com/docs/user/en/bench)
- [Frappe Framework Documentation](https://frappeframework.com/docs)
- [Google AI Studio](https://aistudio.google.com/) - For Chatbot API keys

---

**Version**: 1.0.2  
**Last Updated**: January 19, 2026  
**Maintainer**: Praveen Y
