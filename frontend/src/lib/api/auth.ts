import { request } from './client';

export interface TokenResponse {
	access_token: string;
	token_type: string;
}

export interface UserResponse {
	id: string;
	username: string;
	email?: string;
}

export async function login(username: string, password: string): Promise<TokenResponse> {
	return request<TokenResponse>('/api/auth/login', {
		method: 'POST',
		body: JSON.stringify({ username, password })
	});
}

export async function register(
	username: string,
	password: string,
	email?: string
): Promise<UserResponse> {
	return request<UserResponse>('/api/auth/register', {
		method: 'POST',
		body: JSON.stringify({ username, password, email })
	});
}

export async function getMe(): Promise<UserResponse> {
	return request<UserResponse>('/api/auth/me');
}

export async function logout(): Promise<void> {
	return request<void>('/api/auth/logout', { method: 'POST' });
}

export async function refreshToken(): Promise<TokenResponse> {
	return request<TokenResponse>('/api/auth/refresh', { method: 'POST' });
}
