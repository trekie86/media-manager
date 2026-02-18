export const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

let tokenGetter: (() => string | null) | null = null;

export function setTokenGetter(fn: () => string | null) {
	tokenGetter = fn;
}

export async function request<T>(
	path: string,
	options: RequestInit = {},
	overrideToken?: string | null
): Promise<T> {
	const token = overrideToken !== undefined ? overrideToken : tokenGetter?.() ?? null;

	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...(options.headers as Record<string, string>)
	};

	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}

	const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

	if (!res.ok) {
		const body = await res.json().catch(() => ({ detail: res.statusText }));
		throw new ApiError(res.status, body.detail ?? 'Request failed');
	}

	if (res.status === 204) return undefined as T;
	return res.json() as Promise<T>;
}
