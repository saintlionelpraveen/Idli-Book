# Changelog

All notable changes to Idli Book will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-14

### Added

#### Independent Master DocTypes
- **IB Currency** - Self-contained currency master
  - 50+ pre-loaded global currencies (INR, USD, EUR, GBP, JPY, CNY, etc.)
  - Fields: Currency Code, Name, Symbol, Fraction, Number Format
  - Removes dependency on Frappe Currency master
  
- **IB UOM** - Unit of Measurement master
  - 17 pre-loaded common UOMs (Nos, Kg, Ltr, Box, Meter, etc.)
  - Types: Quantity, Weight, Length, Volume, Area, Time, Other
  - Removes dependency on external UOM master
  
- **IB Country** - Country master
  - 60 pre-loaded major countries worldwide
  - ISO 3166-1 alpha-2 country codes
  - Removes dependency on Frappe Country master

#### Reports
- **IB Customer Growth** - Customer acquisition analysis
  - Time-series chart showing customer growth trends
  - Filters: Date range, Period (Monthly/Quarterly/Yearly)
  - Metrics: New Customers, Total Customers, Growth Rate, Active Customers
  - Mixed chart visualization (bars + lines)

### Changed
- **IB Organization**: `base_currency` now links to IB Currency (was Currency)
- **IB Organization**: `country` now links to IB Country (was Country)
- **IB Item**: `unit_of_measurement` now links to IB UOM (was Data field)

### Technical
- Migration patch: `create_default_currency_uom` auto-creates all master data
- All new DocTypes under "Idli Book" module for consistency
- Complete independence from ERPNext/external modules

---

## [1.0.0] - 2026-01-11

### Added

#### Core Features
- **Complete Accounting System**
  - Chart of Accounts with auto-creation for customers/vendors
  - General Ledger entries for all transactions
  - Trial Balance, Profit & Loss, Balance Sheet reports
  
#### Sales Module
- IB Estimate (Quotations)
- IB Sales Order
- IB Sales Invoice with GL integration
- IB Credit Note (Sales Returns)
- Email delivery with PDF attachment
- Sales reports and dashboards

#### Purchase Module
- IB Purchase Order
- IB Purchase Bill with GL integration
- IB Debit Note (Purchase Returns)
- Purchase reports and vendor tracking

#### Inventory Management
- Item master with stock tracking
- Automatic stock updates on invoice/bill submission
- Low stock alerts
- Inventory reports

#### Payment Processing
- **UPI QR Code Integration**
  - Dynamic QR code generation per invoice
  - `/invoice_payment` public page
  - Email integration with "Pay Now" button
  - Configurable UPI ID and payee name
  
- **Razorpay Integration** (Optional)
  - Payment gateway support
  - Order creation and signature verification
  - Webhook support

- Payment entry with invoice allocation
- Automatic invoice status updates

#### Master Data
- IB Organization (Single DocType for company settings)
- IB Customer with auto-created receivable accounts
- IB Vendor with auto-created payable accounts
- IB Item with inventory tracking
- IB Tax master
- IB State master for GST
- IB HSN/SAC codes

#### Reports (29 Total)
**Financial:**
- Profit & Loss
- Balance Sheet
- Trial Balance

**Sales:**
- Sales Invoice Status
- Estimate Status
- Best Selling Products
- Customer Payment Status (AR Aging)

**Purchase:**
- Purchase Order Status
- Purchase Bill Status
- Vendor Payment Status (AP Aging)
- Total Purchased Products

**Inventory:**
- Inventory Tracked Items
- Low Stock Items

**Summary Cards:**
- Total Customers, Vendors, Items
- Total Income, Expenses
- Total Receivables, Payables
- Top 5 Expenses

#### Workspaces (14 Total)
- Idli Book (Main Dashboard)
- Sales, Purchase, Items
- Payment, Receive, Pay
- Customers, Vendors
- Bills, Purchase Orders
- Sales Invoices, Sales Orders, Estimates

#### Tax & Compliance
- GST calculation (CGST/SGST for intrastate, IGST for interstate)
- Automatic tax splitting based on customer/vendor state
- HSN/SAC code support

### Features

#### Automation
- Auto-create customer receivable accounts on save
- Auto-create vendor payable accounts on save
- Auto-update stock on invoice/bill submission
- Auto-send invoice emails with payment links
- Auto-update invoice status based on payments

#### Email Features
- Email validation before sending
- PDF invoice attachment
- UPI payment link (if enabled)
- Razorpay payment link (if enabled)
- Email delivery status tracking

#### Security
- Email validation to prevent errors
- Payment page error handling
- UPI QR code validation
- Razorpay signature verification

### Technical Details

#### Dependencies
- Frappe Framework v15
- ERPNext v15 (optional)
- Python 3.10+
- qrcode[pil] library for UPI QR generation

#### File Structure
```
idli_book/
├── idli_book/
│   ├── doctype/           # 24 DocTypes
│   ├── report/            # 29 Reports
│   ├── workspace/         # 14 Workspaces
│   ├── page/              # Custom pages
│   ├── www/               # Public web pages
│   │   ├── invoice_payment.py
│   │   ├── invoice_payment.html
│   │   ├── pay.py
│   │   └── pay.html
│   ├── api.py             # Payment APIs
│   └── gl_engine.py       # GL creation logic
└── docs/                  # Documentation
```

### Fixed
- Email validation to prevent "Administrator" email errors
- Payment page 404 errors with correct file paths
- UPI QR code library import handling
- Invoice status update logic
- Customer/Vendor account auto-creation

### Known Issues
- Razorpay integration requires manual configuration
- Email sending requires valid SMTP settings
- UPI payment confirmation is manual (not auto-verified)

---

## Future Roadmap

### Planned Features
- [ ] Automated UPI payment verification
- [ ] Multi-currency support
- [ ] Advanced reporting with charts
- [ ] Mobile app integration
- [ ] Batch payment processing
- [ ] Recurring invoices
- [ ] Purchase requisitions
- [ ] Quotation comparison
- [ ] Budget management

### Under Consideration
- WhatsApp invoice delivery
- Payment reminders
- Credit note approval workflow
- Multi-warehouse support
- Production/Manufacturing module

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.1 | 2026-01-14 | Independent master data (Currency, UOM, Country) |
| 1.0.0 | 2026-01-11 | Initial production release |

---

## Upgrade Notes

### From Development to v1.0.0

1. Run migration:
   ```bash
   bench --site site1.local migrate
   ```

2. Install qrcode library:
   ```bash
   ./env/bin/pip install qrcode[pil]
   ```

3. Configure IB Payment Settings:
   - Set UPI ID
   - Set Payee Name
   - Enable UPI QR Code

4. Configure IB Organization:
   - Set default accounts
   - Set default bank account

---

**Maintainer**: Praveen Y  
**Contact**: jaga03038@gmail.com  
**License**: MIT
