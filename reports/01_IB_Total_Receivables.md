# Report 1: IB Total Receivables - Production Ready

## Report Configuration

```
Report Name: IB Total Receivables
Report Type: Query Report
Ref DocType: IB Sales Invoice
Module: Idli Book
Is Standard: No
```

---

## SQL Query

```sql
SELECT 
    si.customer as "Customer:Link/IB Customer:180",
    si.customer_name as "Customer Name:Data:200",
    COUNT(DISTINCT si.name) as "Invoice Count:Int:100",
    SUM(si.outstanding_amount) as "Total Outstanding:Currency:150",
    SUM(CASE 
        WHEN DATEDIFF(CURDATE(), si.invoice_date) <= 30 
        THEN si.outstanding_amount ELSE 0 
    END) as "0-30 Days:Currency:120",
    SUM(CASE 
        WHEN DATEDIFF(CURDATE(), si.invoice_date) BETWEEN 31 AND 60 
        THEN si.outstanding_amount ELSE 0 
    END) as "31-60 Days:Currency:120",
    SUM(CASE 
        WHEN DATEDIFF(CURDATE(), si.invoice_date) BETWEEN 61 AND 90 
        THEN si.outstanding_amount ELSE 0 
    END) as "61-90 Days:Currency:120",
    SUM(CASE 
        WHEN DATEDIFF(CURDATE(), si.invoice_date) > 90 
        THEN si.outstanding_amount ELSE 0 
    END) as "90+ Days:Currency:120",
    ROUND(AVG(DATEDIFF(CURDATE(), si.invoice_date)), 0) as "Avg Days Outstanding:Int:120",
    MAX(si.invoice_date) as "Last Invoice Date:Date:120"
FROM 
    `tabIB Sales Invoice` si
WHERE 
    si.docstatus = 1
    AND si.outstanding_amount > 0
    AND si.invoice_date BETWEEN %(from_date)s AND %(to_date)s
    {conditions}
GROUP BY 
    si.customer, si.customer_name
ORDER BY 
    SUM(si.outstanding_amount) DESC
```

---

## Filters JSON

```json
[
    {
        "fieldname": "from_date",
        "label": "From Date",
        "fieldtype": "Date",
        "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -12)",
        "reqd": 1
    },
    {
        "fieldname": "to_date",
        "label": "To Date",
        "fieldtype": "Date",
        "default": "frappe.datetime.nowdate()",
        "reqd": 1
    },
    {
        "fieldname": "customer",
        "label": "Customer",
        "fieldtype": "Link",
        "options": "IB Customer"
    }
]
```

---

## Key Features

- **Aging Analysis**: Breaks down outstanding by age buckets
- **Customer Drill-Down**: Clickable customer links
- **Date Range**: Last 12 months by default
- **Sorted**: By highest outstanding first
- **Performance**: Optimized with proper WHERE clause

---

## Business Value

- Identify customers with highest outstanding
- Prioritize collection efforts
- Monitor payment aging
- Cash flow planning
