<script lang="ts">
	import { onMount } from 'svelte';
	import {
		listStorage,
		createStorage,
		updateStorage,
		deleteStorage,
		buildTree,
		type Storage,
		type StorageCreate,
		type StorageType,
		type StorageNode
	} from '$lib/api/storage';
	import { listMovies, type Movie } from '$lib/api/movies';
	import { ApiError } from '$lib/api/client';
	import { toast } from '$lib/stores/toast';

	// ── State ────────────────────────────────────────────────────────────────
	let storageList = $state<Storage[]>([]);
	let tree = $state<StorageNode[]>([]);
	let loading = $state(true);
	let error = $state('');

	let selectedNode = $state<Storage | null>(null);
	let selectedMovies = $state<Movie[]>([]);
	let moviesLoading = $state(false);
	let includeDescendants = $state(true);

	// Modal
	let showModal = $state(false);
	let editTarget = $state<Storage | null>(null);
	let deleteTarget = $state<Storage | null>(null);
	let modalLoading = $state(false);
	let modalError = $state('');
	let parentForNew = $state<string>('');

	// Form
	let formName = $state('');
	let formType = $state<StorageType>('bin');
	let formDescription = $state('');
	let formParentId = $state('');
	let formCapacity = $state<number | ''>('');
	let formLocation = $state('');

	const STORAGE_TYPES: StorageType[] = ['cabinet', 'shelf', 'bin', 'drawer'];
	const TYPE_ICONS: Record<StorageType, string> = {
		cabinet: '🗄️',
		shelf: '📚',
		bin: '📦',
		drawer: '🗂️'
	};

	// ── Lifecycle ─────────────────────────────────────────────────────────────
	onMount(loadStorage);

	async function loadStorage() {
		loading = true;
		error = '';
		try {
			storageList = await listStorage({ limit: 500 });
			tree = buildTree(storageList);
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load storage';
		} finally {
			loading = false;
		}
	}

	async function selectNode(node: Storage) {
		selectedNode = node;
		await reloadMovies();
	}

	async function reloadMovies() {
		if (!selectedNode) return;
		moviesLoading = true;
		selectedMovies = [];
		try {
			selectedMovies = await listMovies({
				storage_id: selectedNode.id,
				include_descendants: includeDescendants,
				limit: 200
			});
		} catch {
			selectedMovies = [];
		} finally {
			moviesLoading = false;
		}
	}

	// Recompute: does the selected node have any descendants?
	let selectedHasChildren = $derived(
		selectedNode ? storageList.some((s) => s.path.includes(selectedNode!.id)) : false
	);

	// For a movie, find its direct storage name (may differ from selectedNode when including descendants)
	function movieStorageName(storageId: string): string {
		return storageList.find((s) => s.id === storageId)?.name ?? '';
	}

	// ── Modal helpers ─────────────────────────────────────────────────────────
	function openCreate(parentId = '') {
		editTarget = null;
		parentForNew = parentId;
		formName = '';
		formType = 'bin';
		formDescription = '';
		formParentId = parentId;
		formCapacity = '';
		formLocation = '';
		modalError = '';
		showModal = true;
	}

	function openEdit(s: Storage) {
		editTarget = s;
		formName = s.name;
		formType = s.type;
		formDescription = s.description ?? '';
		formParentId = s.parent_id ?? '';
		formCapacity = s.metadata?.capacity ?? '';
		formLocation = s.metadata?.location ?? '';
		modalError = '';
		showModal = true;
	}

	function closeModal() {
		showModal = false;
		editTarget = null;
		deleteTarget = null;
	}

	async function handleSave(e: Event) {
		e.preventDefault();
		modalError = '';
		modalLoading = true;
		try {
			const payload: StorageCreate = {
				name: formName.trim(),
				type: formType,
				description: formDescription.trim() || undefined,
				parent_id: formParentId || undefined,
				metadata: {
					capacity: formCapacity !== '' ? Number(formCapacity) : undefined,
					location: formLocation.trim() || undefined
				}
			};
			if (editTarget) {
				await updateStorage(editTarget.id, payload);
			} else {
				await createStorage(payload);
			}
			closeModal();
			toast.success(editTarget ? 'Location updated' : 'Location added');
			await loadStorage();
		} catch (err) {
			modalError = err instanceof ApiError ? err.message : 'Failed to save';
		} finally {
			modalLoading = false;
		}
	}

	async function handleDelete() {
		if (!deleteTarget) return;
		modalLoading = true;
		try {
			await deleteStorage(deleteTarget.id);
			if (selectedNode?.id === deleteTarget.id) {
				selectedNode = null;
				selectedMovies = [];
			}
			toast.success('Location deleted');
			deleteTarget = null;
			await loadStorage();
		} catch (err) {
			toast.error(err instanceof ApiError ? err.message : 'Failed to delete');
			deleteTarget = null;
		} finally {
			modalLoading = false;
		}
	}

	// ── Tree rendering helper ─────────────────────────────────────────────────
	let expandedIds = $state(new Set<string>());

	function toggleExpand(id: string) {
		const next = new Set(expandedIds);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		expandedIds = next;
	}
</script>

<div class="flex h-full">
	<!-- Tree panel -->
	<div class="w-72 flex-shrink-0 bg-white dark:bg-surface-800 border-r border-surface-200 dark:border-surface-700 flex flex-col">
		<div class="px-4 py-3 border-b border-surface-200 dark:border-surface-700 flex items-center justify-between">
			<h3 class="font-semibold text-surface-900 dark:text-surface-50 text-sm">Storage Locations</h3>
			<button
				onclick={() => openCreate()}
				class="text-xs px-2 py-1 rounded-lg bg-primary-500 hover:bg-primary-600 text-white transition-colors"
			>
				+ Add
			</button>
		</div>

		<div class="flex-1 overflow-y-auto p-2">
			{#if loading}
				<div class="flex justify-center py-8">
					<div class="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
				</div>
			{:else if error}
				<p class="text-xs text-error-600 dark:text-error-400 px-2 py-4">{error}</p>
			{:else if tree.length === 0}
				<div class="text-center py-8 text-surface-400">
					<p class="text-2xl mb-2">📦</p>
					<p class="text-xs">No storage locations yet</p>
					<button onclick={() => openCreate()} class="mt-2 text-xs text-primary-500 hover:underline">
						Add one
					</button>
				</div>
			{:else}
				{#snippet treeNode(node: StorageNode, depth: number)}
					<div>
						<div
							class="flex items-center gap-1 px-2 py-1.5 rounded-lg cursor-pointer text-sm transition-colors
								{selectedNode?.id === node.id
									? 'bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300'
									: 'hover:bg-surface-50 dark:hover:bg-surface-700 text-surface-700 dark:text-surface-300'}"
							style="padding-left: {0.5 + depth * 1}rem"
						>
							<!-- Expand toggle -->
							{#if node.children.length > 0}
								<button
									onclick={(e) => { e.stopPropagation(); toggleExpand(node.id); }}
									class="w-4 h-4 flex items-center justify-center text-surface-400 hover:text-surface-600 flex-shrink-0 text-xs"
								>
									{expandedIds.has(node.id) ? '▾' : '▸'}
								</button>
							{:else}
								<span class="w-4 flex-shrink-0"></span>
							{/if}

							<!-- Node label -->
							<button
								onclick={() => selectNode(node)}
								class="flex items-center gap-1.5 flex-1 min-w-0 text-left"
							>
								<span class="flex-shrink-0">{TYPE_ICONS[node.type]}</span>
								<span class="truncate text-xs font-medium">{node.name}</span>
							</button>

							<!-- Actions -->
							<div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 flex-shrink-0">
								<button
									onclick={(e) => { e.stopPropagation(); openCreate(node.id); }}
									class="p-0.5 rounded text-surface-400 hover:text-primary-500"
									title="Add child"
								>
									+
								</button>
								<button
									onclick={(e) => { e.stopPropagation(); openEdit(node); }}
									class="p-0.5 rounded text-surface-400 hover:text-surface-600 dark:hover:text-surface-200"
									title="Edit"
								>
									✏
								</button>
								<button
									onclick={(e) => { e.stopPropagation(); deleteTarget = node; }}
									class="p-0.5 rounded text-surface-400 hover:text-error-500"
									title="Delete"
								>
									✕
								</button>
							</div>
						</div>

						{#if expandedIds.has(node.id) && node.children.length > 0}
							{#each node.children as child}
								{@render treeNode(child, depth + 1)}
							{/each}
						{/if}
					</div>
				{/snippet}

				<div class="space-y-0.5">
					{#each tree as root}
						<!-- Wrap in group for hover actions -->
						<div class="group">
							{@render treeNode(root, 0)}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<!-- Detail panel -->
	<div class="flex-1 overflow-y-auto p-6">
		{#if !selectedNode}
			<div class="flex flex-col items-center justify-center h-full text-surface-400">
				<p class="text-5xl mb-4">📦</p>
				<p class="text-lg font-medium">Select a storage location</p>
				<p class="text-sm mt-1">Click any item in the tree to see its contents</p>
			</div>
		{:else}
			<!-- Storage details -->
			<div class="max-w-2xl">
				<div class="flex items-start justify-between mb-6">
					<div>
						<div class="flex items-center gap-2 mb-1">
							<span class="text-2xl">{TYPE_ICONS[selectedNode.type]}</span>
							<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-50">{selectedNode.name}</h2>
						</div>
						<div class="flex items-center gap-3 text-sm text-surface-500">
							<span class="capitalize px-2 py-0.5 rounded-full bg-surface-100 dark:bg-surface-700 font-medium">
								{selectedNode.type}
							</span>
							{#if selectedNode.metadata?.location}
								<span>📍 {selectedNode.metadata.location}</span>
							{/if}
							{#if selectedNode.metadata?.capacity}
								<span>Capacity: {selectedNode.metadata.capacity}</span>
							{/if}
						</div>
						{#if selectedNode.description}
							<p class="text-sm text-surface-500 mt-2">{selectedNode.description}</p>
						{/if}
					</div>
					<div class="flex gap-2">
						<button
							onclick={() => openEdit(selectedNode!)}
							class="px-3 py-1.5 text-sm rounded-lg border border-surface-200 dark:border-surface-600 text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-700 transition-colors"
						>
							Edit
						</button>
						<button
							onclick={() => (deleteTarget = selectedNode)}
							class="px-3 py-1.5 text-sm rounded-lg border border-error-200 dark:border-error-800 text-error-600 dark:text-error-400 hover:bg-error-50 dark:hover:bg-error-950 transition-colors"
						>
							Delete
						</button>
					</div>
				</div>

				<!-- Path breadcrumb -->
				{#if selectedNode.path.length > 0}
					<div class="mb-6 flex items-center gap-1 text-xs text-surface-400">
						<span>Location:</span>
						{#each selectedNode.path as pathId}
							{#each storageList.filter(s => s.id === pathId) as ancestor}
								<span>{ancestor.name}</span>
								<span>›</span>
							{/each}
						{/each}
						<span class="text-surface-600 dark:text-surface-300 font-medium">{selectedNode.name}</span>
					</div>
				{/if}

				<!-- Movies in this storage -->
				<div>
					<div class="flex items-center justify-between mb-3">
						<div class="flex items-center gap-3 flex-wrap">
							<h3 class="font-semibold text-surface-800 dark:text-surface-200">
								Movies
								{#if selectedMovies.length > 0}
									<span class="ml-1 text-sm font-normal text-surface-400">({selectedMovies.length})</span>
								{/if}
							</h3>
							{#if selectedHasChildren}
								<label class="flex items-center gap-1.5 cursor-pointer select-none">
									<input
										type="checkbox"
										bind:checked={includeDescendants}
										onchange={reloadMovies}
										class="w-3.5 h-3.5 rounded accent-primary-500"
									/>
									<span class="text-xs text-surface-500">include sub-locations</span>
								</label>
							{/if}
						</div>
						<a
							href="/movies?storage_id={selectedNode.id}&include_descendants={includeDescendants && selectedHasChildren ? 'true' : 'false'}"
							class="text-xs text-primary-500 hover:underline"
						>
							View all →
						</a>
					</div>

					{#if moviesLoading}
						<div class="flex justify-center py-8">
							<div class="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
						</div>
					{:else if selectedMovies.length === 0}
						<div class="text-center py-8 border border-dashed border-surface-200 dark:border-surface-700 rounded-xl text-surface-400">
							<p class="text-sm">
								{includeDescendants && selectedHasChildren
									? 'No movies in this location or its sub-locations'
									: 'No movies directly in this location'}
							</p>
						</div>
					{:else}
						<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
							{#each selectedMovies as movie (movie.id)}
								<div class="bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 overflow-hidden">
									<div class="aspect-[2/3] bg-surface-100 dark:bg-surface-700">
										{#if movie.cover_image}
											<img src={movie.cover_image} alt={movie.title} class="w-full h-full object-cover" loading="lazy" />
										{:else}
											<div class="w-full h-full flex items-center justify-center text-surface-400 text-3xl">🎬</div>
										{/if}
									</div>
									<div class="p-2">
										<p class="text-xs font-semibold text-surface-900 dark:text-surface-50 line-clamp-2 leading-tight">{movie.title}</p>
										<p class="text-xs text-surface-400">{movie.year} · {movie.format}</p>
										{#if includeDescendants && movie.storage_id !== selectedNode.id}
											<p class="text-xs text-surface-400 mt-0.5 truncate" title={movieStorageName(movie.storage_id)}>
												📦 {movieStorageName(movie.storage_id)}
											</p>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- Add / Edit Modal -->
{#if showModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div class="absolute inset-0 bg-black/50" onclick={closeModal}></div>
		<div class="relative bg-white dark:bg-surface-800 rounded-2xl shadow-2xl w-full max-w-md">
			<div class="px-6 py-4 border-b border-surface-200 dark:border-surface-700 flex items-center justify-between">
				<h3 class="text-lg font-semibold text-surface-900 dark:text-surface-50">
					{editTarget ? 'Edit Storage' : 'Add Storage Location'}
				</h3>
				<button onclick={closeModal} class="text-surface-400 hover:text-surface-600 text-xl leading-none">✕</button>
			</div>

			<form onsubmit={handleSave} class="px-6 py-5 space-y-4">
				{#if modalError}
					<div class="p-3 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200 text-sm">
						{modalError}
					</div>
				{/if}

				<div>
					<label for="st-name" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
						Name <span class="text-error-500">*</span>
					</label>
					<input
						id="st-name"
						type="text"
						bind:value={formName}
						required
						class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
						placeholder="e.g. Living Room Cabinet"
					/>
				</div>

				<div>
					<label for="st-type" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
						Type <span class="text-error-500">*</span>
					</label>
					<select
						id="st-type"
						bind:value={formType}
						class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
					>
						{#each STORAGE_TYPES as t}
							<option value={t}>{TYPE_ICONS[t]} {t.charAt(0).toUpperCase() + t.slice(1)}</option>
						{/each}
					</select>
				</div>

				<div>
					<label for="st-parent" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
						Parent Location
					</label>
					<select
						id="st-parent"
						bind:value={formParentId}
						class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
					>
						<option value="">None (top-level)</option>
						{#each storageList.filter(s => !editTarget || s.id !== editTarget.id) as s}
							<option value={s.id}>{TYPE_ICONS[s.type]} {s.name}</option>
						{/each}
					</select>
				</div>

				<div>
					<label for="st-desc" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
						Description
					</label>
					<input
						id="st-desc"
						type="text"
						bind:value={formDescription}
						class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
						placeholder="Optional description"
					/>
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div>
						<label for="st-capacity" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
							Capacity
						</label>
						<input
							id="st-capacity"
							type="number"
							bind:value={formCapacity}
							min="1"
							class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
							placeholder="Max items"
						/>
					</div>

					<div>
						<label for="st-location" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
							Location
						</label>
						<input
							id="st-location"
							type="text"
							bind:value={formLocation}
							class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
							placeholder="e.g. Basement"
						/>
					</div>
				</div>

				<div class="flex justify-end gap-3 pt-2">
					<button type="button" onclick={closeModal} class="px-4 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-700 transition-colors">
						Cancel
					</button>
					<button
						type="submit"
						disabled={modalLoading}
						class="px-4 py-2 text-sm rounded-lg bg-primary-500 hover:bg-primary-600 disabled:opacity-50 text-white font-medium transition-colors"
					>
						{modalLoading ? 'Saving…' : editTarget ? 'Save Changes' : 'Add Location'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- Delete confirmation -->
{#if deleteTarget}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div class="absolute inset-0 bg-black/50" onclick={() => (deleteTarget = null)}></div>
		<div class="relative bg-white dark:bg-surface-800 rounded-2xl shadow-2xl w-full max-w-sm p-6">
			<h3 class="text-lg font-semibold text-surface-900 dark:text-surface-50 mb-2">Delete Storage</h3>
			<p class="text-sm text-surface-600 dark:text-surface-400 mb-6">
				Are you sure you want to delete <strong>{deleteTarget.name}</strong>?
				This will fail if it has children or movies assigned.
			</p>
			<div class="flex justify-end gap-3">
				<button onclick={() => (deleteTarget = null)} class="px-4 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-700 transition-colors">
					Cancel
				</button>
				<button
					onclick={handleDelete}
					disabled={modalLoading}
					class="px-4 py-2 text-sm rounded-lg bg-error-500 hover:bg-error-600 disabled:opacity-50 text-white font-medium transition-colors"
				>
					{modalLoading ? 'Deleting…' : 'Delete'}
				</button>
			</div>
		</div>
	</div>
{/if}
