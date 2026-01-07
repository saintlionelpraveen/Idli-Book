frappe.ui.form.on('IB Sales Invoice', {
    setup: function (frm) {
        // Efficient fetching
        frm.add_fetch('item_code', 'item_name', 'item_name');
        frm.add_fetch('item_code', 'sales_description', 'description');
        frm.add_fetch('item_code', 'unit', 'uom');
        frm.add_fetch('item_code', 'selling_price', 'rate');
        frm.add_fetch('item_code', 'tax_percentage', 'tax_rate');
    },

    refresh: function (frm) {
        // Payment Status Indicator
        if (frm.doc.docstatus === 1) {
            let status_html = '';
            if (frm.doc.status === 'Paid') {
                status_html = `<div style="padding: 8px; background: #d4edda; color: #155724; border-radius: 4px; margin-bottom: 10px;">
                    <strong>✓ Fully Paid</strong> - Total: ₹${format_currency(frm.doc.grand_total)}
                </div>`;
            } else if (frm.doc.status === 'Partially Paid') {
                status_html = `<div style="padding: 8px; background: #fff3cd; color: #856404; border-radius: 4px; margin-bottom: 10px;">
                    <strong>⚠ Partially Paid</strong> - Due: ₹${format_currency(frm.doc.outstanding_amount)}
                </div>`;
            } else if (frm.doc.status === 'Awaiting Payment' || frm.doc.status === 'Overdue') {
                status_html = `<div style="padding: 8px; background: #f8d7da; color: #721c24; border-radius: 4px; margin-bottom: 10px;">
                    <strong>⏳ Payment Due</strong> - ₹${format_currency(frm.doc.outstanding_amount)}
                </div>`;
            }
            if (status_html) frm.set_intro(status_html, 'blue');

            // Payment Button
            if (frm.doc.outstanding_amount > 0.01) {
                frm.add_custom_button(__('Record Payment'), function () {
                    frappe.new_doc('IB Payment', {
                        payment_type: 'Receive',
                        party_type: 'IB Customer',
                        party: frm.doc.customer,
                        amount: frm.doc.outstanding_amount,
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
        }
    },

    onload: function (frm) {
        // Auto-fetch Billing Address from IB Organization (Single)
        if (frm.is_new()) {
            frappe.db.get_single_value('IB Organization', 'organization_name').then(name => {
                // We fetch the whole doc because get_single_value relies on field names being top level
                frappe.call({
                    method: 'frappe.client.get',
                    args: { doctype: 'IB Organization' },
                    callback: function (r) {
                        if (r.message) {
                            let org = r.message;
                            let address_parts = [
                                org.organization_name,
                                org.street_address_1,
                                org.street_address_2,
                                org.city,
                                org.state_province,
                                org.zip_postal_code,
                                org.country
                            ].filter(Boolean); // Remove empty values

                            frm.set_value('billing_address', address_parts.join('\n'));
                        }
                    }
                });
            });
        }
    },

    customer: function (frm) {
        if (frm.doc.customer) {
            // Fetch Shipping Address & State (Place of Supply) from Customer
            frappe.db.get_value('IB Customer', frm.doc.customer, ['shipping_address', 'billing_address', 'state'], (r) => {
                if (r) {
                    // 1. Shipping Address (Preferred: shipping field, Fallback: billing field)
                    if (r.shipping_address) {
                        frm.set_value('shipping_address', r.shipping_address);
                    } else if (r.billing_address) {
                        frm.set_value('shipping_address', r.billing_address);
                    }

                    // 2. Place of Supply
                    if (r.state) {
                        frm.set_value('place_of_supply', r.state);
                    }
                }
            });
        }
    },

    // Date Validation
    due_date: function (frm) { validate_dates(frm); },
    invoice_date: function (frm) { validate_dates(frm); },

    // Totals triggers
    adjustment: function (frm) { calculate_totals(frm); }
});

function validate_dates(frm) {
    if (frm.doc.invoice_date && frm.doc.due_date) {
        if (frm.doc.due_date < frm.doc.invoice_date) {
            frappe.msgprint({
                title: __('Invalid Date'),
                message: __('Due Date cannot be before Invoice Date'),
                indicator: 'red'
            });
            frm.set_value('due_date', '');
        }
    }
}

frappe.ui.form.on('IB Invoice Item', {
    item_code: function (frm, cdt, cdn) {
        // Set default quantity
        let row = locals[cdt][cdn];
        if (!row.quantity) frappe.model.set_value(cdt, cdn, 'quantity', 1);
    },

    quantity: function (frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    rate: function (frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    tax_rate: function (frm, cdt, cdn) { calculate_row(frm, cdt, cdn); }
});

var calculate_row = function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let qty = row.quantity || 0;
    let rate = row.rate || 0;

    // Simple Amount
    let amount = qty * rate;
    frappe.model.set_value(cdt, cdn, 'amount', amount);

    // Tax
    let tax_amt = (amount * (row.tax_rate || 0)) / 100;
    frappe.model.set_value(cdt, cdn, 'tax_amount', tax_amt);

    calculate_totals(frm);
};

var calculate_totals = function (frm) {
    let subtotal = 0;
    let total_tax = 0;

    (frm.doc.items || []).forEach(item => {
        subtotal += item.amount || 0;
        total_tax += item.tax_amount || 0;
    });

    frm.set_value('subtotal', subtotal);
    frm.set_value('tax_amount', total_tax);

    let grand_total = subtotal + total_tax + (frm.doc.adjustment || 0);
    frm.set_value('grand_total', grand_total);

    // Update Outstanding immediately if draft, else driven by payment
    if (frm.doc.docstatus === 0) {
        frm.set_value('outstanding_amount', grand_total);
    }

    // Visual Refresh
    frm.refresh_field('subtotal');
    frm.refresh_field('tax_amount');
    frm.refresh_field('grand_total');
    frm.refresh_field('items');
};
