frappe.ui.form.on('IB Sales Invoice', {
    setup: function (frm) {
        frm.add_fetch('tax', 'tax_rate', 'tax_rate');
    },
    refresh: function (frm) {
        // Show payment status indicator
        if (frm.doc.docstatus === 1) {
            let status_html = '';
            let status_color = '';

            if (frm.doc.status === 'Paid') {
                status_html = `<div style="padding: 8px; background: #d4edda; color: #155724; border-radius: 4px; margin-bottom: 10px;">
                    <strong>✓ Fully Paid</strong> - Total: ₹${format_currency(frm.doc.grand_total)} | Paid: ₹${format_currency(frm.doc.paid_amount)}
                </div>`;
            } else if (frm.doc.status === 'Partially Paid') {
                status_html = `<div style="padding: 8px; background: #fff3cd; color: #856404; border-radius: 4px; margin-bottom: 10px;">
                    <strong>⚠ Partially Paid</strong> - Total: ₹${format_currency(frm.doc.grand_total)} | Paid: ₹${format_currency(frm.doc.paid_amount)} | <strong>Due: ₹${format_currency(frm.doc.outstanding_amount)}</strong>
                </div>`;
            } else if (frm.doc.status === 'Awaiting Payment') {
                status_html = `<div style="padding: 8px; background: #f8d7da; color: #721c24; border-radius: 4px; margin-bottom: 10px;">
                    <strong>⏳ Awaiting Payment</strong> - Total: ₹${format_currency(frm.doc.grand_total)} | <strong>Due: ₹${format_currency(frm.doc.outstanding_amount)}</strong>
                </div>`;
            }

            if (status_html) {
                frm.set_intro(status_html, 'blue');
            }
        }

        // Add Payment button only if outstanding amount exists
        if (frm.doc.docstatus === 1 && frm.doc.outstanding_amount > 0.01) {
            frm.add_custom_button(__('Record Payment'), function () {
                frappe.route_options = {
                    "linked_invoice": frm.doc.name
                };
                frappe.new_doc('IB Payment', {
                    payment_type: 'Receive',
                    party_type: 'IB Customer',
                    party: frm.doc.customer,
                    amount: frm.doc.outstanding_amount,
                    // Pre-fill the reference table
                    references: [{
                        reference_doctype: "IB Sales Invoice",
                        reference_name: frm.doc.name,
                        total_amount: frm.doc.grand_total,
                        outstanding_amount: frm.doc.outstanding_amount,
                        allocated_amount: frm.doc.outstanding_amount
                    }]
                });
            });
        }
    },
    customer: function (frm) {
        if (frm.doc.customer) {
            frappe.db.get_value('IB Customer', frm.doc.customer, ['billing_address'], (r) => {
                if (r) {
                    frm.set_value('billing_address', r.billing_address);
                    frm.set_value('shipping_address', r.billing_address);
                }
            });
        }
    },
    discount_type: function (frm) {
        calculate_totals(frm);
    },
    discount_percentage: function (frm) {
        if (frm.doc.discount_type == 'Percentage') {
            calculate_totals(frm);
        }
    },
    discount_amount: function (frm) {
        if (frm.doc.discount_type == 'Amount') {
            calculate_totals(frm);
        }
    }
});

frappe.ui.form.on('IB Invoice Item', {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'IB Item',
                    name: row.item_code
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'item_name', r.message.item_name);
                        frappe.model.set_value(cdt, cdn, 'description', r.message.sales_description);
                        frappe.model.set_value(cdt, cdn, 'uom', r.message.unit);
                        frappe.model.set_value(cdt, cdn, 'rate', r.message.selling_price);
                    }
                }
            });
        }
    },
    quantity: function (frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    rate: function (frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    discount_type: function (frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    discount_percentage: function (frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    discount_amount: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let base_amount = row.quantity * row.rate;
        if (base_amount > 0) {
            frappe.model.set_value(cdt, cdn, 'discount_percentage', (row.discount_amount / base_amount) * 100);
        }
        calculate_item_amount(frm, cdt, cdn, true);
    },
    tax: function (frm, cdt, cdn) {
        // Tax rate auto-fetches via setup
    },
    tax_rate: function (frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    }
});

var calculate_item_amount = function (frm, cdt, cdn, skip_discount_amount_update) {
    let row = locals[cdt][cdn];
    let base_amount = row.quantity * row.rate;
    let discount = 0;

    if (row.discount_type == 'Percentage') {
        discount = (base_amount * row.discount_percentage) / 100;
        if (!skip_discount_amount_update) {
            frappe.model.set_value(cdt, cdn, 'discount_amount', discount);
        }
    } else {
        discount = row.discount_amount;
        if (base_amount > 0 && !skip_discount_amount_update) {
            frappe.model.set_value(cdt, cdn, 'discount_percentage', (discount / base_amount) * 100);
        }
    }

    let amount = base_amount - discount;
    frappe.model.set_value(cdt, cdn, 'amount', amount);

    // Tax Calculation
    let tax_rate = row.tax_rate || 0;
    let tax_amount = (amount * tax_rate) / 100;
    frappe.model.set_value(cdt, cdn, 'tax_amount', tax_amount);

    calculate_totals(frm);
};

var calculate_totals = function (frm) {
    let subtotal = 0;

    // Subtotal = Sum of all line item amounts (already after line-level discounts)
    frm.doc.items.forEach(function (item) {
        subtotal += item.amount || 0;
    });

    // Header-level Discount
    let discount_type = frm.doc.discount_type || 'Percentage';
    let discount = 0;

    if (discount_type == 'Percentage') {
        discount = (subtotal * (frm.doc.discount_percentage || 0)) / 100;
        frm.set_value('discount_amount', discount);
    } else {
        // Amount type
        discount = frm.doc.discount_amount || 0;
        if (subtotal > 0) {
            frm.set_value('discount_percentage', (discount / subtotal) * 100);
        }
    }

    // Net Total after discount
    let net_total = subtotal - discount;

    // Tax on Net Total (sum of line item taxes)
    let total_tax = 0;
    frm.doc.items.forEach(function (item) {
        total_tax += item.tax_amount || 0;
    });

    // Grand Total
    let grand_total = net_total + total_tax;

    // Set Header Fields
    frm.set_value('subtotal', subtotal);
    frm.set_value('tax_amount', total_tax);
    frm.set_value('grand_total', grand_total);
    frm.set_value('outstanding_amount', grand_total - (frm.doc.paid_amount || 0));
};
