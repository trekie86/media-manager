import { request } from './client';

export type MovieFormat = 'DVD' | 'Blu-ray' | 'Digital';

export interface Movie {
	id: string;
	title: string;
	year: number;
	format: MovieFormat;
	storage_id: string;
	tmdb_id?: number;
	genre?: string[];
	runtime?: number;
	cover_image?: string;
}

export interface MovieCreate {
	title: string;
	year: number;
	format: MovieFormat;
	storage_id: string;
	tmdb_id?: number;
	genre?: string[];
	runtime?: number;
	cover_image?: string;
}

export interface MovieUpdate {
	title?: string;
	year?: number;
	format?: MovieFormat;
	storage_id?: string;
	tmdb_id?: number;
	genre?: string[];
	runtime?: number;
	cover_image?: string;
}

export interface MovieFilters {
	skip?: number;
	limit?: number;
	storage_id?: string;
	format?: string;
	genre?: string;
}

export interface TmdbSearchResult {
	results: TmdbMovie[];
	total_results: number;
	page: number;
	total_pages: number;
}

export interface TmdbMovie {
	id: number;
	title: string;
	release_date?: string;
	overview?: string;
	poster_path?: string;
	backdrop_path?: string;
	genre_ids?: number[];
}

export async function listMovies(filters: MovieFilters = {}): Promise<Movie[]> {
	const params = new URLSearchParams();
	if (filters.skip != null) params.set('skip', String(filters.skip));
	if (filters.limit != null) params.set('limit', String(filters.limit));
	if (filters.storage_id) params.set('storage_id', filters.storage_id);
	if (filters.format) params.set('format', filters.format);
	if (filters.genre) params.set('genre', filters.genre);
	const qs = params.toString();
	return request<Movie[]>(`/api/movies/${qs ? `?${qs}` : ''}`);
}

export async function searchMovies(q: string, filters: MovieFilters = {}): Promise<Movie[]> {
	const params = new URLSearchParams({ q });
	if (filters.skip != null) params.set('skip', String(filters.skip));
	if (filters.limit != null) params.set('limit', String(filters.limit));
	if (filters.storage_id) params.set('storage_id', filters.storage_id);
	if (filters.format) params.set('format', filters.format);
	if (filters.genre) params.set('genre', filters.genre);
	return request<Movie[]>(`/api/movies/search?${params.toString()}`);
}

export async function getMovie(id: string): Promise<Movie> {
	return request<Movie>(`/api/movies/${id}`);
}

export async function createMovie(data: MovieCreate): Promise<Movie> {
	return request<Movie>('/api/movies/', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updateMovie(id: string, data: MovieUpdate): Promise<Movie> {
	return request<Movie>(`/api/movies/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function deleteMovie(id: string): Promise<void> {
	return request<void>(`/api/movies/${id}`, { method: 'DELETE' });
}

export async function searchTmdb(q: string, year?: number): Promise<TmdbSearchResult> {
	const params = new URLSearchParams({ q });
	if (year) params.set('year', String(year));
	return request<TmdbSearchResult>(`/api/movies/tmdb/search?${params.toString()}`);
}

export async function enrichMovie(id: string): Promise<Movie> {
	return request<Movie>(`/api/movies/${id}/enrich`, { method: 'POST' });
}
