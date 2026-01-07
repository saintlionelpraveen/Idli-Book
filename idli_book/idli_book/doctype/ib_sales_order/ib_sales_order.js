// Copy the same calculation logic from Estimate to Sales Order
frappe.ui.form.on('IB Sales Order', {
    setup: function (frm) {
        // Native fetching configured in DocType JSON for best performance
    },
    refresh: function (frm) {
        // Add Create Invoice button (only after submit)
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Invoice'), function () {
                frappe.call({
                    method: 'idli_book.idli_book.doctype.ib_sales_order.ib_sales_order.make_sales_invoice',
                    args: {
                        source_name: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.model.sync(r.message);
                            frappe.set_route('Form', 'IB Sales Invoice', r.message.name);
                        }
                    }
                });
            }, __('Create'));
        }
    },
    validate: function (frm) {
        if (frm.doc.shipment_date && frm.doc.order_date) {
            if (frm.doc.shipment_date < frm.doc.order_date) {
                frappe.msgprint(__('Shipment Date cannot be before Order Date'));
                frappe.validated = false;
            }
        }
    },
    discount_type: function (frm) {
        calculate_totals(frm);
    },
    discount_percentage: function (frm) {
        calculate_totals(frm);
    },
    discount_amount: function (frm) {
        calculate_totals(frm);
    }
});

frappe.ui.form.on('IB Invoice Item', {
    // item_code trigger removed - handled by add_fetch in setup

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
        calculate_item_amount(frm, cdt, cdn);
    },
    tax: function (frm, cdt, cdn) {
        // Tax rate auto-fetches
    },
    tax_rate: function (frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    }
});

var calculate_item_amount = function (frm, cdt, cdn, skip_sync) {
    let row = locals[cdt][cdn];

    // Guard against invalid data
    if (!row || !row.quantity || !row.rate) return;

    let base_amount = row.quantity * row.rate;
    let discount = 0;

    if (row.discount_type == 'Percentage') {
        discount = (base_amount * (row.discount_percentage || 0)) / 100;
        // Use SILENT update to prevent triggering discount_amount event
        frappe.model.set_value(cdt, cdn, 'discount_amount', discount, null, true);
    } else {
        discount = row.discount_amount || 0;
        if (base_amount > 0) {
            // Use SILENT update to prevent triggering discount_percentage event
            frappe.model.set_value(cdt, cdn, 'discount_percentage', (discount / base_amount) * 100, null, true);
        }
    }

    let amount = base_amount - discount;

    // Tax Calculation
    let tax_rate = row.tax_rate || 0;
    let tax_amount = (amount * tax_rate) / 100;

    // Batch update with silent flag
    frappe.model.set_value(cdt, cdn, 'amount', amount, null, true);
    frappe.model.set_value(cdt, cdn, 'tax_amount', tax_amount, null, true);

    // Only recalculate totals if not in a sync operation
    if (!skip_sync) {
        calculate_totals(frm);
    }
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
};
