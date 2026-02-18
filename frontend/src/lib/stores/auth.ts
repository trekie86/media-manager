import { writable, get } from 'svelte/store';
import { setTokenGetter } from '$lib/api/client';

export interface AuthUser {
	username: string;
}

interface AuthState {
	token: string | null;
	user: AuthUser | null;
}

const TOKEN_KEY = 'mm_token';

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>({
		token: null,
		user: null
	});

	return {
		subscribe,

		/** Call once on app mount to restore session from localStorage */
		init() {
			const token = localStorage.getItem(TOKEN_KEY);
			if (token) {
				update((s) => ({ ...s, token }));
			}
		},

		login(token: string, user: AuthUser) {
			localStorage.setItem(TOKEN_KEY, token);
			set({ token, user });
		},

		setUser(user: AuthUser) {
			update((s) => ({ ...s, user }));
		},

		logout() {
			localStorage.removeItem(TOKEN_KEY);
			set({ token: null, user: null });
		},

		getToken(): string | null {
			return get({ subscribe }).token;
		},

		isAuthenticated(): boolean {
			return get({ subscribe }).token !== null;
		}
	};
}

export const auth = createAuthStore();

// Wire the auth store into the API client so every request auto-includes the token
setTokenGetter(() => auth.getToken());
