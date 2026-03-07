import { request } from './client';

export interface TokenResponse {
	access_token: string;
	token_type: string;
}

export interface UserResponse {
	email: string;
	display_name: string;
	avatar_url?: string;
	role: 'admin' | 'read_only';
	status: 'pending' | 'approved';
}

export interface PendingUser {
	id: string;
	email: string;
	display_name: string;
	provider: string;
	status: string;
}

export function getGoogleLoginUrl(): string {
	return `/api/auth/google/login`;
}

export function getGithubLoginUrl(): string {
	return `/api/auth/github/login`;
}

export async function getMe(): Promise<UserResponse> {
	return request<UserResponse>('/api/auth/me');
}

export async function logout(): Promise<void> {
	return request<void>('/api/auth/logout', { method: 'POST' });
}

export async function listPendingUsers(): Promise<PendingUser[]> {
	return request<PendingUser[]>('/api/auth/users/pending');
}

export async function approveUser(userId: string): Promise<UserResponse> {
	return request<UserResponse>(`/api/auth/users/${userId}/approve`, { method: 'POST' });
}

export async function rejectUser(userId: string): Promise<void> {
	return request<void>(`/api/auth/users/${userId}/reject`, { method: 'POST' });
}
