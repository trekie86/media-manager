import { writable } from 'svelte/store';

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
	id: number;
	type: ToastType;
	message: string;
}

let nextId = 0;

function createToastStore() {
	const { subscribe, update } = writable<Toast[]>([]);

	function add(type: ToastType, message: string, durationMs = 3500) {
		const id = ++nextId;
		update((toasts) => [...toasts, { id, type, message }]);
		setTimeout(() => remove(id), durationMs);
	}

	function remove(id: number) {
		update((toasts) => toasts.filter((t) => t.id !== id));
	}

	return {
		subscribe,
		success: (msg: string) => add('success', msg),
		error: (msg: string) => add('error', msg, 5000),
		info: (msg: string) => add('info', msg),
		remove
	};
}

export const toast = createToastStore();
