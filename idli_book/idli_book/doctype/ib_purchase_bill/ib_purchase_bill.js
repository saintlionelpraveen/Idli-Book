frappe.ui.form.on('IB Purchase Bill', {
    refresh: function (frm) {
        // Show payment status indicator with detailed info
        if (frm.doc.docstatus === 1) {
            let status_html = '';

            if (frm.doc.status === 'Paid') {
                status_html = `<div style="padding: 10px; background: #d4edda; color: #155724; border-radius: 6px; margin-bottom: 12px; border-left: 4px solid #28a745;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                        <span style="font-size: 20px;">✓</span>
                        <strong style="font-size: 15px;">Fully Paid</strong>
                    </div>
                    <div style="font-size: 13px; margin-left: 28px;">
                        <span>Vendor: <strong>${frm.doc.vendor}</strong></span><br>
                        <span>Total: ₹${format_currency(frm.doc.grand_total)}</span> | 
                        <span>Paid: ₹${format_currency(frm.doc.paid_amount)}</span>
                    </div>
                </div>`;
            } else if (frm.doc.status === 'Partially Paid') {
                status_html = `<div style="padding: 10px; background: #fff3cd; color: #856404; border-radius: 6px; margin-bottom: 12px; border-left: 4px solid #ffc107;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                        <span style="font-size: 20px;">⚠</span>
                        <strong style="font-size: 15px;">Partially Paid</strong>
                    </div>
                    <div style="font-size: 13px; margin-left: 28px;">
                        <span>Vendor: <strong>${frm.doc.vendor}</strong></span><br>
                        <span>Total: ₹${format_currency(frm.doc.grand_total)}</span> | 
                        <span>Paid: ₹${format_currency(frm.doc.paid_amount)}</span> | 
                        <span style="color: #d9534f;"><strong>Due: ₹${format_currency(frm.doc.outstanding_amount)}</strong></span>
                    </div>
                </div>`;
            } else if (frm.doc.status === 'Awaiting Payment') {
                status_html = `<div style="padding: 10px; background: #f8d7da; color: #721c24; border-radius: 6px; margin-bottom: 12px; border-left: 4px solid #dc3545;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                        <span style="font-size: 20px;">⏳</span>
                        <strong style="font-size: 15px;">Awaiting Payment</strong>
                    </div>
                    <div style="font-size: 13px; margin-left: 28px;">
                        <span>Vendor: <strong>${frm.doc.vendor}</strong></span><br>
                        <span>Total: ₹${format_currency(frm.doc.grand_total)}</span> | 
                        <span style="color: #d9534f;"><strong>Due: ₹${format_currency(frm.doc.outstanding_amount)}</strong></span>
                    </div>
                </div>`;
            }

            if (status_html) {
                frm.set_intro(status_html, 'blue');
            }
        }

        // Add Record Payment button only if outstanding amount exists
        if (frm.doc.docstatus === 1 && frm.doc.outstanding_amount > 0.01) {
            frm.add_custom_button(__('Record Payment'), function () {
                frappe.route_options = {
                    "linked_invoice": frm.doc.name
                };
                frappe.new_doc('IB Payment', {
                    payment_type: 'Pay',
                    party_type: 'IB Vendor',
                    party: frm.doc.vendor,
                    amount: frm.doc.outstanding_amount,
                    references: [{
                        reference_doctype: "IB Purchase Bill",
                        reference_name: frm.doc.name,
                        total_amount: frm.doc.grand_total,
                        outstanding_amount: frm.doc.outstanding_amount,
                        allocated_amount: frm.doc.outstanding_amount
                    }]
                });
            }, __('Actions'));
        }
    }
});
