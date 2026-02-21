import { request } from './client';

export interface Genre {
	id: number;
	name: string;
}

export async function listGenres(): Promise<Genre[]> {
	return request<Genre[]>('/api/genres/');
}
