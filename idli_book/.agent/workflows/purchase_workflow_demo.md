---
description: Purchase Module Workflow Demo
---

# 🛒 Purchase Module Workflow: From Order to Payment

This guide walks you through the complete purchasing cycle in **Idli Book** using example data.

## 🎭 Scenario
You run a printing business and need to buy paper stock.
*   **You**: Idli Book Admin
*   **Vendor**: "Paper Kings Ltd"
*   **Item**: "A4 Premium Paper (500 Sheets)"

---

## 1️⃣ Step 1: Create a Vendor
If you haven't already, add the supplier details.
1.  Go to **IB Vendor List**.
2.  Click **Add IB Vendor**.
3.  **Vendor Name**: `Paper Kings Ltd`
4.  **Email**: `orders@paperkings.com` (Use your own email to test notifications!)
5.  **State**: `Karnataka` (For GST calculations)
6.  **Save**.

## 2️⃣ Step 2: Create a Purchase Order (PO)
Check prices and confirm the order with the vendor.
1.  Go to **IB Purchase Order**.
2.  Click **Add IB Purchase Order**.
3.  **Vendor**: Select `Paper Kings Ltd`.
4.  **Items Table**:
    *   **Item**: `A4 Premium Paper` (Create this item if missing, Buying Price: ₹200).
    *   **Quantity**: `50`
    *   **Rate**: `₹200`
5.  **Delivery Date**: Select a date 3 days from now.
6.  **Save** and **Submit**.
    *   ✨ **Automation**: The vendor (`orders@paperkings.com`) automatically receives a professional email with the PO attached.

## 3️⃣ Step 3: Receive the Bill (Purchase Invoice)
The goods have arrived, and the vendor sent their invoice #PK-9988.
1.  Open the **IB Purchase Order** you just created.
2.  Click the **Create Purchase Bill** button (Top Right).
3.  The system auto-fills everything.
4.  **Reference #**: Enter the Vendor's Invoice Number (`PK-9988`).
5.  **Save** and **Submit**.
    *   ✅ **Accounting**: "Accounts Payable" increases (You owe money).
    *   ✅ **Stock**: "A4 Premium Paper" inventory count increases by 50.

## 4️⃣ Step 4: Make Payment
You pay the vendor via Bank Transfer.
1.  Open the **IB Purchase Bill** you just created.
2.  Click the **Make Payment** button (Top Right).
    *   *Or go to IB Payment > Payment Type: "Pay"*.
3.  **Payment Mode**: `Bank Transfer`.
4.  **Amount**: The system auto-fills the outstanding amount (e.g., ₹10,000 + Tax).
5.  **Save** and **Submit**.
    *   ✨ **Automation**: The vendor receives a "Payment Advice" email confirming you have paid.
    *   ✅ **Accounting**: Your "Bank" account decreases, and "Accounts Payable" is cleared.
    *   ✅ **Status**: Purchase Bill marked as "Paid".

---

## 📊 Summary of Effects
| Action | Financial Effect (GL) | Stock Effect |
| :--- | :--- | :--- |
| **Purchase Order** | No Entry (Just a commitment) | None (Pending Receipt) |
| **Purchase Bill** | Credit: Accounts Payable (Liability)<br>Debit: Expense/Asset (Cost) | **+50** Stock Qty |
| **Payment (Pay)** | Debit: Accounts Payable (Liability)<br>Credit: Bank (Asset) | None |
