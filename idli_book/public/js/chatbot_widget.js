frappe.provide('frappe.ui');

frappe.ui.ChatbotWidget = class ChatbotWidget {
    constructor() {
        this.setup();
    }

    setup() {
        this.make_widget();
        this.bind_events();
    }

    make_widget() {
        // Create floating button
        this.$button = $(`
			<div class="chatbot-widget-button" title="Idli Book Assistant">
				<svg style="width: 28px; height: 28px; fill: white;" viewBox="0 0 24 24">
					<path d="M12,3C6.5,3 2,6.58 2,11C2.05,13.15 3.06,15.17 4.75,16.5C4.75,17.1 4.33,18.67 2,21C4.37,20.89 6.64,20 8.47,18.5C9.61,18.83 10.81,19 12,19C17.5,19 22,15.42 22,11C22,6.58 17.5,3 12,3M12,17C7.58,17 4,14.31 4,11C4,7.69 7.58,5 12,5C16.42,5 20,7.69 20,11C20,14.31 16.42,17 12,17Z"/>
				</svg>
			</div>
		`).appendTo('body');

        // Create chat popup
        this.$popup = $(`
			<div class="chatbot-widget-popup" style="display: none;">
				<div class="chatbot-widget-header">
					<div class="chatbot-widget-title">
						<svg style="width: 20px; height: 20px; fill: white; margin-right: 8px;" viewBox="0 0 24 24">
							<path d="M12,3C6.5,3 2,6.58 2,11C2.05,13.15 3.06,15.17 4.75,16.5C4.75,17.1 4.33,18.67 2,21C4.37,20.89 6.64,20 8.47,18.5C9.61,18.83 10.81,19 12,19C17.5,19 22,15.42 22,11C22,6.58 17.5,3 12,3M12,17C7.58,17 4,14.31 4,11C4,7.69 7.58,5 12,5C16.42,5 20,7.69 20,11C20,14.31 16.42,17 12,17Z"/>
						</svg>
						<span>Idli Book Assistant</span>
					</div>
					<button class="chatbot-widget-close">&times;</button>
				</div>
				<div class="chatbot-widget-messages"></div>
				<div class="chatbot-widget-input-area">
					<input type="text" class="chatbot-widget-input" placeholder="Ask me anything..." />
					<button class="chatbot-widget-send">
						<svg style="width: 20px; height: 20px; fill: white;" viewBox="0 0 24 24">
							<path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/>
						</svg>
					</button>
				</div>
			</div>
		`).appendTo('body');

        this.$messages = this.$popup.find('.chatbot-widget-messages');
        this.$input = this.$popup.find('.chatbot-widget-input');
        this.$send = this.$popup.find('.chatbot-widget-send');

        this.add_styles();
    }

    add_styles() {
        if ($('#chatbot-widget-styles').length) return;

        $('head').append(`
			<style id="chatbot-widget-styles">
				.chatbot-widget-button {
					position: fixed;
					bottom: 20px;
					right: 20px;
					width: 60px;
					height: 60px;
					background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
					border-radius: 50%;
					display: flex;
					align-items: center;
					justify-content: center;
					cursor: pointer;
					box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
					z-index: 9998;
					transition: all 0.3s ease;
				}

				.chatbot-widget-button:hover {
					transform: scale(1.1);
					box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
				}

				.chatbot-widget-popup {
					position: fixed;
					bottom: 90px;
					right: 20px;
					width: 380px;
					height: 500px;
					background: white;
					border-radius: 12px;
					box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
					z-index: 9999;
					display: flex;
					flex-direction: column;
					overflow: hidden;
				}

				.chatbot-widget-header {
					background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
					color: white;
					padding: 16px 20px;
					display: flex;
					justify-content: space-between;
					align-items: center;
				}

				.chatbot-widget-title {
					display: flex;
					align-items: center;
					font-weight: 600;
					font-size: 16px;
				}

				.chatbot-widget-close {
					background: none;
					border: none;
					color: white;
					font-size: 28px;
					cursor: pointer;
					line-height: 1;
					padding: 0;
					width: 30px;
					height: 30px;
					display: flex;
					align-items: center;
					justify-content: center;
					border-radius: 4px;
					transition: background 0.2s;
				}

				.chatbot-widget-close:hover {
					background: rgba(255, 255, 255, 0.2);
				}

				.chatbot-widget-messages {
					flex: 1;
					overflow-y: auto;
					padding: 20px;
					background: #f8f9fa;
				}

				.chatbot-message {
					margin-bottom: 16px;
					display: flex;
					gap: 8px;
				}

				.chatbot-message.user {
					flex-direction: row-reverse;
				}

				.chatbot-message-bubble {
					max-width: 75%;
					padding: 12px 16px;
					border-radius: 12px;
					word-wrap: break-word;
				}

				.chatbot-message.user .chatbot-message-bubble {
					background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
					color: white;
					border-bottom-right-radius: 4px;
				}

				.chatbot-message.assistant .chatbot-message-bubble {
					background: white;
					color: #333;
					border-bottom-left-radius: 4px;
					box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
				}

				.chatbot-widget-input-area {
					display: flex;
					gap: 8px;
					padding: 16px;
					background: white;
					border-top: 1px solid #e0e0e0;
				}

				.chatbot-widget-input {
					flex: 1;
					padding: 10px 16px;
					border: 1px solid #e0e0e0;
					border-radius: 20px;
					outline: none;
					font-size: 14px;
				}

				.chatbot-widget-input:focus {
					border-color: #667eea;
				}

				.chatbot-widget-send {
					width: 40px;
					height: 40px;
					background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
					border: none;
					border-radius: 50%;
					cursor: pointer;
					display: flex;
					align-items: center;
					justify-content: center;
					transition: all 0.2s;
				}

				.chatbot-widget-send:hover {
					transform: scale(1.05);
				}

				.chatbot-widget-send:disabled {
					opacity: 0.5;
					cursor: not-allowed;
				}

				.chatbot-typing {
					display: flex;
					gap: 4px;
					padding: 12px 16px;
				}

				.chatbot-typing span {
					width: 8px;
					height: 8px;
					background: #999;
					border-radius: 50%;
					animation: typing 1.4s infinite;
				}

				.chatbot-typing span:nth-child(2) { animation-delay: 0.2s; }
				.chatbot-typing span:nth-child(3) { animation-delay: 0.4s; }

				@keyframes typing {
					0%, 60%, 100% { transform: translateY(0); }
					30% { transform: translateY(-10px); }
				}
			</style>
		`);
    }

    bind_events() {
        // Toggle popup
        this.$button.on('click', () => this.toggle_popup());
        this.$popup.find('.chatbot-widget-close').on('click', () => this.hide_popup());

        // Send message
        this.$send.on('click', () => this.send_message());
        this.$input.on('keypress', (e) => {
            if (e.which === 13) this.send_message();
        });
    }

    toggle_popup() {
        if (this.$popup.is(':visible')) {
            this.hide_popup();
        } else {
            this.show_popup();
        }
    }

    show_popup() {
        this.$popup.fadeIn(200);
        this.$input.focus();

        // Welcome message if first time
        if (this.$messages.children().length === 0) {
            this.add_message('assistant', 'Hello! I\'m your Idli Book Assistant. Ask me about invoices, customers, payments, or business summaries.');
        }
    }

    hide_popup() {
        this.$popup.fadeOut(200);
    }

    add_message(role, content) {
        const $message = $(`
			<div class="chatbot-message ${role}">
				<div class="chatbot-message-bubble">${frappe.utils.escape_html(content)}</div>
			</div>
		`);
        this.$messages.append($message);
        this.$messages.scrollTop(this.$messages[0].scrollHeight);
    }

    show_typing() {
        const $typing = $(`
			<div class="chatbot-message assistant chatbot-typing-indicator">
				<div class="chatbot-message-bubble chatbot-typing">
					<span></span><span></span><span></span>
				</div>
			</div>
		`);
        this.$messages.append($typing);
        this.$messages.scrollTop(this.$messages[0].scrollHeight);
    }

    hide_typing() {
        this.$messages.find('.chatbot-typing-indicator').remove();
    }

    async send_message() {
        const message = this.$input.val().trim();
        if (!message) return;

        // Add user message
        this.add_message('user', message);
        this.$input.val('');
        this.$send.prop('disabled', true);

        // Show typing
        this.show_typing();

        try {
            const response = await frappe.call({
                method: 'idli_book.api.chatbot.chat',
                args: { message }
            });

            this.hide_typing();

            if (response.message.response) {
                this.add_message('assistant', response.message.response);
            } else {
                this.add_message('assistant', 'Sorry, I couldn\'t process that request.');
            }
        } catch (error) {
            this.hide_typing();
            this.add_message('assistant', 'Sorry, I encountered an error. Please try again.');
            console.error('Chatbot error:', error);
        } finally {
            this.$send.prop('disabled', false);
            this.$input.focus();
        }
    }
};

// Initialize on page load
$(document).on('app_ready', function () {
    frappe.chatbot_widget = new frappe.ui.ChatbotWidget();
});
