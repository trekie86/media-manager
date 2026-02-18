import { request } from './client';

export type StorageType = 'cabinet' | 'shelf' | 'bin' | 'drawer';

export interface StorageMetadata {
	capacity?: number;
	dimensions?: string;
	location?: string;
}

export interface Storage {
	id: string;
	name: string;
	description?: string;
	type: StorageType;
	parent_id?: string | null;
	path: string[];
	metadata?: StorageMetadata;
}

export interface StorageCreate {
	name: string;
	type: StorageType;
	description?: string;
	parent_id?: string;
	metadata?: StorageMetadata;
}

export interface StorageUpdate {
	name?: string;
	type?: StorageType;
	description?: string;
	parent_id?: string;
	metadata?: StorageMetadata;
}

export interface StorageFilters {
	parent_id?: string;
	type?: StorageType;
	skip?: number;
	limit?: number;
}

export async function listStorage(filters: StorageFilters = {}): Promise<Storage[]> {
	const params = new URLSearchParams();
	if (filters.parent_id) params.set('parent_id', filters.parent_id);
	if (filters.type) params.set('type', filters.type);
	if (filters.skip != null) params.set('skip', String(filters.skip));
	if (filters.limit != null) params.set('limit', String(filters.limit));
	const qs = params.toString();
	return request<Storage[]>(`/api/storage${qs ? `?${qs}` : ''}`);
}

export async function getStorage(id: string): Promise<Storage> {
	return request<Storage>(`/api/storage/${id}`);
}

export async function createStorage(data: StorageCreate): Promise<Storage> {
	return request<Storage>('/api/storage', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updateStorage(id: string, data: StorageUpdate): Promise<Storage> {
	return request<Storage>(`/api/storage/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function deleteStorage(id: string): Promise<void> {
	return request<void>(`/api/storage/${id}`, { method: 'DELETE' });
}

/** Build a nested tree from a flat list of storage nodes */
export interface StorageNode extends Storage {
	children: StorageNode[];
}

export function buildTree(flat: Storage[]): StorageNode[] {
	const map = new Map<string, StorageNode>();
	const roots: StorageNode[] = [];

	for (const s of flat) {
		map.set(s.id, { ...s, children: [] });
	}

	for (const node of map.values()) {
		if (node.parent_id && map.has(node.parent_id)) {
			map.get(node.parent_id)!.children.push(node);
		} else {
			roots.push(node);
		}
	}

	return roots;
}
