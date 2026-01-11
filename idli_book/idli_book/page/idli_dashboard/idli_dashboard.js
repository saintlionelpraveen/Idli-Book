frappe.pages['idli-dashboard'].on_page_load = function (wrapper) {
	new ZohoDashboard(wrapper);
};

class ZohoDashboard {
	constructor(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Dashboard',
			single_column: true
		});

		this.wrapper = wrapper;
		this.filters = {
			period: 'This Month',
			from_date: frappe.datetime.month_start(),
			to_date: frappe.datetime.get_today()
		};

		this.setup();
	}

	setup() {
		this.add_filters();
		this.render();
		this.load_data();
	}

	add_filters() {
		const me = this;

		// Period Filter
		this.page.add_field({
			label: 'Period',
			fieldtype: 'Select',
			fieldname: 'period',
			options: [
				'Today',
				'This Week',
				'This Month',
				'This Quarter',
				'This Year',
				'Last Month',
				'Last Quarter',
				'Custom'
			],
			default: 'This Month',
			change: function () {
				const val = this.get_value();
				if (val === 'Custom') {
					me.show_custom_dates();
				} else {
					me.set_dates(val);
					me.load_data();
				}
			}
		});

		this.page.set_secondary_action('Refresh', () => this.load_data());
	}

	set_dates(period) {
		const today = frappe.datetime.get_today();
		let from_date, to_date;

		switch (period) {
			case 'Today':
				from_date = to_date = today;
				break;
			case 'This Week':
				from_date = frappe.datetime.week_start();
				to_date = today;
				break;
			case 'This Month':
				from_date = frappe.datetime.month_start();
				to_date = today;
				break;
			case 'This Quarter':
				from_date = frappe.datetime.quarter_start();
				to_date = today;
				break;
			case 'This Year':
				from_date = frappe.datetime.year_start();
				to_date = today;
				break;
			case 'Last Month':
				from_date = frappe.datetime.add_months(frappe.datetime.month_start(), -1);
				to_date = frappe.datetime.month_end(from_date);
				break;
			case 'Last Quarter':
				from_date = frappe.datetime.add_months(frappe.datetime.quarter_start(), -3);
				to_date = frappe.datetime.add_days(frappe.datetime.quarter_start(), -1);
				break;
		}

		this.filters = { period, from_date, to_date };
	}

	show_custom_dates() {
		const me = this;
		const d = new frappe.ui.Dialog({
			title: 'Select Date Range',
			fields: [
				{ fieldtype: 'Date', fieldname: 'from_date', label: 'From', reqd: 1 },
				{ fieldtype: 'Date', fieldname: 'to_date', label: 'To', reqd: 1 }
			],
			primary_action_label: 'Apply',
			primary_action: (v) => {
				me.filters.from_date = v.from_date;
				me.filters.to_date = v.to_date;
				me.load_data();
				d.hide();
			}
		});
		d.show();
	}

	render() {
		const $main = $(this.wrapper).find('.layout-main-section');
		$main.empty().append(`
			<div class="container-fluid px-4 py-3">
				<!-- KPI Cards -->
				<div class="row g-3 mb-4">
					<div class="col-md-3">
						<div class="card border-0 shadow-sm h-100 kpi-card" data-doctype="IB Sales Invoice">
							<div class="card-body">
								<h6 class="text-muted mb-2">Receivables</h6>
								<h3 class="mb-1 kpi-value" id="val-receivable">₹ 0</h3>
								<small class="text-muted">Outstanding invoices</small>
							</div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="card border-0 shadow-sm h-100 kpi-card" data-doctype="IB Purchase Bill">
							<div class="card-body">
								<h6 class="text-muted mb-2">Payables</h6>
								<h3 class="mb-1 kpi-value" id="val-payable">₹ 0</h3>
								<small class="text-muted">Outstanding bills</small>
							</div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="card border-0 shadow-sm h-100 kpi-card">
							<div class="card-body">
								<h6 class="text-muted mb-2">Revenue</h6>
								<h3 class="mb-1 kpi-value" id="val-revenue">₹ 0</h3>
								<small class="text-muted">For selected period</small>
							</div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="card border-0 shadow-sm h-100 kpi-card">
							<div class="card-body">
								<h6 class="text-muted mb-2">Profit</h6>
								<h3 class="mb-1 kpi-value" id="val-profit">₹ 0</h3>
								<small class="text-muted">Net income</small>
							</div>
						</div>
					</div>
				</div>
				
				<!-- Charts Row -->
				<div class="row g-3 mb-4">
					<div class="col-md-8">
						<div class="card border-0 shadow-sm">
							<div class="card-header bg-white border-bottom">
								<h5 class="mb-0">Cash Flow</h5>
							</div>
							<div class="card-body">
								<div id="chart-cashflow"></div>
							</div>
						</div>
					</div>
					<div class="col-md-4">
						<div class="card border-0 shadow-sm">
							<div class="card-header bg-white border-bottom">
								<h5 class="mb-0">Income vs Expense</h5>
							</div>
							<div class="card-body">
								<div id="chart-income"></div>
							</div>
						</div>
					</div>
				</div>
				
				<!-- Tables Row -->
				<div class="row g-3">
					<div class="col-md-6">
						<div class="card border-0 shadow-sm">
							<div class="card-header bg-white border-bottom">
								<h5 class="mb-0">Bank & Cash Accounts</h5>
							</div>
							<div class="card-body p-0">
								<div class="table-responsive">
									<table class="table table-hover mb-0" id="accounts-table">
										<tbody></tbody>
									</table>
								</div>
							</div>
						</div>
					</div>
					<div class="col-md-6">
						<div class="card border-0 shadow-sm">
							<div class="card-header bg-white border-bottom">
								<h5 class="mb-0">Recent Transactions</h5>
							</div>
							<div class="card-body p-0">
								<div class="table-responsive">
									<table class="table table-hover mb-0" id="txn-table">
										<tbody></tbody>
									</table>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			
			<style>
				.kpi-card {
					cursor: pointer;
					transition: transform 0.2s, box-shadow 0.2s;
				}
				.kpi-card:hover {
					transform: translateY(-4px);
					box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15) !important;
				}
				.kpi-value {
					font-size: 2rem;
					font-weight: 700;
				}
				.card-header h5 {
					font-size: 1rem;
					font-weight: 600;
				}
			</style>
		`);

		// Add click handlers
		const me = this;
		$main.find('.kpi-card').on('click', function () {
			const doctype = $(this).data('doctype');
			if (doctype) {
				frappe.set_route('List', doctype);
			}
		});
	}

	load_data() {
		const me = this;
		frappe.call({
			method: 'idli_book.idli_book.page.idli_dashboard.idli_dashboard.get_dashboard_data',
			args: {
				period: this.filters.period,
				from_date: this.filters.from_date,
				to_date: this.filters.to_date
			},
			freeze: true,
			callback: (r) => {
				if (r.message) me.update(r.message);
			}
		});
	}

	update(data) {
		// Update values
		$('#val-receivable').text(frappe.format(data.outstanding_summary.receivable, { fieldtype: 'Currency' }));
		$('#val-payable').text(frappe.format(data.outstanding_summary.payable, { fieldtype: 'Currency' }));
		$('#val-revenue').text(frappe.format(data.summary_cards.revenue, { fieldtype: 'Currency' }));

		const profit = data.summary_cards.profit;
		$('#val-profit')
			.text(frappe.format(profit, { fieldtype: 'Currency' }))
			.css('color', profit >= 0 ? '#28a745' : '#dc3545');

		// Charts
		if (data.cash_flow_chart && data.cash_flow_chart.labels) {
			new frappe.Chart('#chart-cashflow', {
				data: {
					labels: data.cash_flow_chart.labels,
					datasets: [
						{ name: 'In', values: data.cash_flow_chart.cash_in },
						{ name: 'Out', values: data.cash_flow_chart.cash_out }
					]
				},
				type: 'bar',
				height: 250,
				colors: ['#28a745', '#dc3545']
			});
		}

		if (data.income_vs_expense && data.income_vs_expense.labels) {
			new frappe.Chart('#chart-income', {
				data: {
					labels: data.income_vs_expense.labels.slice(-6),
					datasets: [
						{ name: 'Income', values: data.income_vs_expense.income.slice(-6) },
						{ name: 'Expense', values: data.income_vs_expense.expense.slice(-6) }
					]
				},
				type: 'line',
				height: 250,
				colors: ['#007bff', '#ffc107']
			});
		}

		// Accounts table
		const accounts = data.bank_balance.accounts || [];
		let acc_html = accounts.length === 0
			? '<tr><td class="text-center text-muted p-3">No accounts</td></tr>'
			: accounts.map(a => `
				<tr>
					<td class="p-3">${a.account}</td>
					<td class="p-3 text-end fw-bold" style="color: ${a.balance >= 0 ? '#28a745' : '#dc3545'}">
						${frappe.format(a.balance, { fieldtype: 'Currency' })}
					</td>
				</tr>
			`).join('');
		$('#accounts-table tbody').html(acc_html);

		// Transactions table
		const txns = data.recent_transactions || [];
		let txn_html = txns.length === 0
			? '<tr><td class="text-center text-muted p-3">No transactions</td></tr>'
			: txns.map(t => `
				<tr>
					<td class="p-3">
						<div class="fw-bold">${frappe.datetime.str_to_user(t.date)}</div>
						<small class="text-muted">${t.customer || '-'}</small>
					</td>
					<td class="p-3 text-end">
						<div class="fw-bold">${frappe.format(t.amount, { fieldtype: 'Currency' })}</div>
						<small class="text-muted">${t.type}</small>
					</td>
				</tr>
			`).join('');
		$('#txn-table tbody').html(txn_html);
	}
}
