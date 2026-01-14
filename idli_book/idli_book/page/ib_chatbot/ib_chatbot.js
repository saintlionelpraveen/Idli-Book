frappe.pages['ib-chatbot'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Idli Book Assistant',
        single_column: true
    });

    new ChatbotUI(page);
};

class ChatbotUI {
    constructor(page) {
        this.page = page;
        this.session_id = null;
        this.messages = [];
        this.make();
    }

    make() {
        this.page.main.html(`
			<style>
				.chatbot-container {
					display: flex;
					flex-direction: column;
					height: calc(100vh - 200px);
					max-width: 900px;
					margin: 0 auto;
					background: white;
					border-radius: 8px;
					box-shadow: 0 2px 8px rgba(0,0,0,0.1);
				}

				.chat-header {
					padding: 20px;
					background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
					color: white;
					border-radius: 8px 8px 0 0;
					display: flex;
					align-items: center;
					justify-content: space-between;
				}

				.chat-header h3 {
					margin: 0;
					font-size: 20px;
				}

				.chat-suggestions {
					padding: 15px;
					background: #f8f9fa;
					border-bottom: 1px solid #e0e0e0;
					display: flex;
					flex-wrap: wrap;
					gap: 8px;
				}

				.suggestion-btn {
					padding: 6px 12px;
					background: white;
					border: 1px solid #ddd;
					border-radius: 20px;
					cursor: pointer;
					font-size: 13px;
					transition: all 0.2s;
				}

				.suggestion-btn:hover {
					background: #667eea;
					color: white;
					border-color: #667eea;
				}

				.chat-messages {
					flex: 1;
					overflow-y: auto;
					padding: 20px;
					display: flex;
					flex-direction: column;
					gap: 15px;
				}

				.chat-message {
					display: flex;
					align-items: flex-start;
					gap: 10px;
					max-width: 80%;
				}

				.chat-message.user {
					align-self: flex-end;
					flex-direction: row-reverse;
				}

				.message-avatar {
					width: 36px;
					height: 36px;
					border-radius: 50%;
					display: flex;
					align-items: center;
					justify-content: center;
					font-weight: bold;
					font-size: 16px;
				}

				.message-avatar.bot {
					background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
					color: white;
				}

				.message-avatar.user {
					background: #4CAF50;
					color: white;
				}

				.message-content {
					padding: 12px 16px;
					border-radius: 18px;
					word-wrap: break-word;
				}

				.chat-message.bot .message-content {
					background: #f1f3f4;
					color: #333;
				}

				.chat-message.user .message-content {
					background: #667eea;
					color: white;
				}

				.message-data {
					margin-top: 10px;
					padding: 10px;
					background: white;
					border: 1px solid #e0e0e0;
					border-radius: 8px;
					font-size: 13px;
				}

				.typing-indicator {
					display: none;
					align-items: center;
					gap: 5px;
					padding: 10px 15px;
					background: #f1f3f4;
					border-radius: 18px;
					width: fit-content;
				}

				.typing-indicator.show {
					display: flex;
				}

				.typing-dot {
					width: 8px;
					height: 8px;
					border-radius: 50%;
					background: #999;
					animation: typing 1.4s infinite;
				}

				.typing-dot:nth-child(2) { animation-delay: 0.2s; }
				.typing-dot:nth-child(3) { animation-delay: 0.4s; }

				@keyframes typing {
					0%, 60%, 100% { transform: translateY(0); }
					30% { transform: translateY(-10px); }
				}

				.chat-input-wrapper {
					padding: 15px;
					background: white;
					border-top: 1px solid #e0e0e0;
					display: flex;
					gap: 10px;
					align-items: center;
				}

				.chat-input {
					flex: 1;
					padding: 12px 16px;
					border: 1px solid #ddd;
					border-radius: 24px;
					font-size: 14px;
					outline: none;
				}

				.chat-input:focus {
					border-color: #667eea;
				}

				.send-btn {
					width: 48px;
					height: 48px;
					border-radius: 50%;
					background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
					color: white;
					border: none;
					cursor: pointer;
					display: flex;
					align-items: center;
					justify-content: center;
					transition: transform 0.2s;
				}

				.send-btn:hover {
					transform: scale(1.1);
				}

				.send-btn:disabled {
					opacity: 0.5;
					cursor: not-allowed;
				}
			</style>

			<div class="chatbot-container">
				<div class="chat-header">
					<div>
						<h3>🤖 Idli Book Assistant</h3>
						<small>Ask me anything about your business</small>
					</div>
					<button class="btn btn-sm btn-light" id="clear-chat">Clear Chat</button>
				</div>
				
				<div class="chat-suggestions" id="suggestions"></div>
				
				<div class="chat-messages" id="chat-messages">
					<div class="chat-message bot">
						<div class="message-avatar bot">AI</div>
						<div class="message-content">
							👋 Hi! I'm your Idli Book assistant. I can help you with:
							<br><br>
							• Check invoice status<br>
							• View customer information<br>
							• Get business summaries<br>
							• And much more!
							<br><br>
Try asking me something like "Show unpaid invoices" or "List all customers"
						</div>
					</div>
					
					<div class="typing-indicator" id="typing-indicator">
						<div class="typing-dot"></div>
						<div class="typing-dot"></div>
						<div class="typing-dot"></div>
					</div>
				</div>
				
				<div class="chat-input-wrapper">
					<input 
						type="text" 
						id="chat-input" 
						class="chat-input"
						placeholder="Type your message..."
						autocomplete="off"
					>
					<button class="send-btn" id="send-btn">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="22" y1="2" x2="11" y2="13"></line>
							<polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
						</svg>
					</button>
				</div>
			</div>
		`);

        this.bind_events();
        this.load_suggestions();
    }

    bind_events() {
        const me = this;

        $('#send-btn').on('click', () => me.send_message());

        $('#chat-input').on('keypress', (e) => {
            if (e.which === 13 && !e.shiftKey) {
                e.preventDefault();
                me.send_message();
            }
        });

        $('#clear-chat').on('click', () => me.clear_chat());
    }

    async load_suggestions() {
        try {
            const res = await frappe.call({
                method: 'idli_book.api.chatbot.get_suggestions'
            });

            const suggestions = res.message.suggestions;
            const $container = $('#suggestions');

            suggestions.forEach(suggestion => {
                const $btn = $(`<button class="suggestion-btn">${suggestion}</button>`);
                $btn.on('click', () => {
                    $('#chat-input').val(suggestion);
                    this.send_message();
                });
                $container.append($btn);
            });
        } catch (error) {
            console.error('Failed to load suggestions:', error);
        }
    }

    async send_message() {
        const $input = $('#chat-input');
        const message = $input.val().trim();

        if (!message) return;

        // Disable input
        $input.prop('disabled', true);
        $('#send-btn').prop('disabled', true);

        // Show user message
        this.add_message('user', message);
        $input.val('');

        // Show typing indicator
        this.show_typing();

        try {
            const res = await frappe.call({
                method: 'idli_book.api.chatbot.chat',
                args: {
                    message: message,
                    session_id: this.session_id
                }
            });

            this.hide_typing();

            const response = res.message;
            this.session_id = response.session_id;

            // Show bot response
            this.add_message('bot', response.response, response.data);

        } catch (error) {
            this.hide_typing();
            this.add_message('bot', 'Sorry, I encountered an error. Please try again.');
            console.error('Chat error:', error);
        } finally {
            // Re-enable input
            $input.prop('disabled', false);
            $('#send-btn').prop('disabled', false);
            $input.focus();
        }
    }

    add_message(role, text, data = null) {
        const $messages = $('#chat-messages');
        const $typing = $('#typing-indicator');

        const avatar = role === 'user' ? frappe.user.abbr() : 'AI';
        const avatarClass = role === 'user' ? 'user' : 'bot';

        let dataHtml = '';
        if (data && Array.isArray(data)) {
            dataHtml = `
				<div class="message-data">
					<table class="table table-sm">
						<tbody>
							${data.slice(0, 5).map(item => `
								<tr>
									<td>${JSON.stringify(item)}</td>
								</tr>
							`).join('')}
						</tbody>
					</table>
					${data.length > 5 ? `<small><i>Showing 5 of ${data.length} results</i></small>` : ''}
				</div>
			`;
        }

        const $msg = $(`
			<div class="chat-message ${role}">
				<div class="message-avatar ${avatarClass}">${avatar}</div>
				<div>
					<div class="message-content">${frappe.utils.escape_html(text)}</div>
					${dataHtml}
				</div>
			</div>
		`);

        $typing.before($msg);
        $messages.scrollTop($messages[0].scrollHeight);
    }

    show_typing() {
        $('#typing-indicator').addClass('show');
        const $messages = $('#chat-messages');
        $messages.scrollTop($messages[0].scrollHeight);
    }

    hide_typing() {
        $('#typing-indicator').removeClass('show');
    }

    clear_chat() {
        if (confirm('Clear all messages?')) {
            $('#chat-messages').find('.chat-message:not(:first)').remove();
            this.session_id = null;
            this.messages = [];
        }
    }
}
