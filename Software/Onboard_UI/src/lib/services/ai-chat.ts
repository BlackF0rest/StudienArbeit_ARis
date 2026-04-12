export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	createdAt: string;
}

export interface ChatProvider {
	name: string;
	enabled: boolean;
	request: (history: ChatMessage[], prompt: string) => Promise<string>;
}

const HISTORY_KEY = 'aris.ai-chat.history';

export function loadHistory(): ChatMessage[] {
	if (typeof localStorage === 'undefined') return [];
	const raw = localStorage.getItem(HISTORY_KEY);
	if (!raw) return [];
	try {
		return JSON.parse(raw) as ChatMessage[];
	} catch {
		return [];
	}
}

export function saveHistory(history: ChatMessage[]): void {
	if (typeof localStorage === 'undefined') return;
	localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 40)));
}

export class DemoChatProvider implements ChatProvider {
	name = 'demo-local';
	enabled = true;

	async request(_history: ChatMessage[], prompt: string): Promise<string> {
		return `Demo-Antwort: \"${prompt}\" wurde lokal verarbeitet.`;
	}
}

export class ApiChatProvider implements ChatProvider {
	name = 'api';
	enabled = false;

	async request(history: ChatMessage[], prompt: string): Promise<string> {
		const response = await fetch('http://localhost:5000/api/ai-chat', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ history, prompt })
		});

		if (!response.ok) {
			throw new Error(`ai-chat returned ${response.status}`);
		}

		const payload = (await response.json()) as { reply?: string };
		return payload.reply ?? 'Keine Antwort vom Provider.';
	}
}

export function createChatProvider(enableApi = false): ChatProvider {
	if (enableApi) {
		const provider = new ApiChatProvider();
		provider.enabled = true;
		return provider;
	}
	return new DemoChatProvider();
}

export function newMessage(role: ChatMessage['role'], content: string): ChatMessage {
	return {
		id: crypto.randomUUID(),
		role,
		content,
		createdAt: new Date().toISOString()
	};
}
