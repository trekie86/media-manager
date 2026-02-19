<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import {
		listMovies,
		searchMovies,
		createMovie,
		updateMovie,
		deleteMovie,
		enrichMovie,
		searchTmdb,
		getTmdbMovie,
		type Movie,
		type MovieCreate,
		type MovieFormat,
		type TmdbMovie
	} from '$lib/api/movies';
	import { listStorage, buildTree, type Storage, type StorageNode } from '$lib/api/storage';
	import { ApiError } from '$lib/api/client';
	import { toast } from '$lib/stores/toast';

	// ── State ────────────────────────────────────────────────────────────────
	let movies = $state<Movie[]>([]);
	let storageList = $state<Storage[]>([]);
	let storageTree = $state<StorageNode[]>([]);
	let loading = $state(true);
	let error = $state('');

	// Filters
	let filterFormat = $state('');
	let filterStorage = $state('');
	let filterGenre = $state('');
	// When a storage filter is active, include movies from descendant nodes by default.
	// This can be seeded from the URL param (e.g. when navigating from the storage page).
	let filterIncludeDescendants = $state(true);

	// Search
	let searchQuery = $state($page.url.searchParams.get('q') ?? '');

	// Flatten tree into depth-ordered list for dropdown (preserves hierarchy visually)
	function flattenTree(nodes: StorageNode[], depth = 0): { storage: Storage; depth: number }[] {
		const result: { storage: Storage; depth: number }[] = [];
		for (const node of nodes) {
			result.push({ storage: node, depth });
			if (node.children.length > 0) {
				result.push(...flattenTree(node.children, depth + 1));
			}
		}
		return result;
	}

	// Reactive flattened storage list ordered by hierarchy for the dropdown
	let storageOptions = $derived(flattenTree(storageTree));

	// Whether the currently selected storage has children (i.e., descendants exist)
	let selectedStorageHasChildren = $derived(
		filterStorage ? storageList.some((s) => s.path.includes(filterStorage)) : false
	);

	// Modal state
	let showModal = $state(false);
	let editMovie = $state<Movie | null>(null);
	let deleteTarget = $state<Movie | null>(null);
	let modalLoading = $state(false);
	let modalError = $state('');

	// Form fields
	let formTitle = $state('');
	let formYear = $state(new Date().getFullYear());
	let formFormat = $state<MovieFormat>('DVD');
	let formStorageId = $state('');
	let formGenre = $state('');
	let formRuntime = $state<number | ''>('');
	let formCoverImage = $state('');
	let formTmdbId = $state<number | undefined>(undefined);

	// TMDB search inside modal
	let tmdbQuery = $state('');
	let tmdbResults = $state<TmdbMovie[]>([]);
	let tmdbSearching = $state(false);

	const FORMATS: MovieFormat[] = ['DVD', 'Blu-ray', 'Digital'];

	// ── Lifecycle ────────────────────────────────────────────────────────────
	onMount(async () => {
		// Restore storage filter from URL (e.g. when arriving from the storage page).
		// include_descendants defaults to true; the storage page passes 'false' explicitly
		// when the user had the toggle off.
		const urlStorageId = $page.url.searchParams.get('storage_id') ?? '';
		const urlDescendantsParam = $page.url.searchParams.get('include_descendants');
		if (urlStorageId) {
			filterStorage = urlStorageId;
			if (urlDescendantsParam !== null) {
				filterIncludeDescendants = urlDescendantsParam === 'true';
			}
		}
		await Promise.all([loadMovies(), loadStorage()]);
	});

	// React to URL search param changes
	$effect(() => {
		const q = $page.url.searchParams.get('q') ?? '';
		if (q !== searchQuery) {
			searchQuery = q;
			loadMovies();
		}
	});

	// ── Data loading ─────────────────────────────────────────────────────────
	async function loadMovies() {
		loading = true;
		error = '';
		try {
			const filters = {
				format: filterFormat || undefined,
				storage_id: filterStorage || undefined,
				include_descendants: filterStorage ? filterIncludeDescendants : undefined,
				genre: filterGenre || undefined,
				limit: 200
			};
			if (searchQuery.trim()) {
				movies = await searchMovies(searchQuery.trim(), filters);
			} else {
				movies = await listMovies(filters);
			}
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load movies';
		} finally {
			loading = false;
		}
	}

	async function loadStorage() {
		try {
			storageList = await listStorage({ limit: 500 });
			storageTree = buildTree(storageList);
		} catch {
			// Non-critical
		}
	}

	function storageName(id: string): string {
		return storageList.find((s) => s.id === id)?.name ?? id;
	}

	// ── Modal helpers ─────────────────────────────────────────────────────────
	function openCreate() {
		editMovie = null;
		formTitle = '';
		formYear = new Date().getFullYear();
		formFormat = 'DVD';
		formStorageId = storageList[0]?.id ?? '';
		formGenre = '';
		formRuntime = '';
		formCoverImage = '';
		formTmdbId = undefined;
		tmdbQuery = '';
		tmdbResults = [];
		modalError = '';
		showModal = true;
	}

	function openEdit(m: Movie) {
		editMovie = m;
		formTitle = m.title;
		formYear = m.year;
		formFormat = m.format;
		formStorageId = m.storage_id;
		formGenre = m.genre?.join(', ') ?? '';
		formRuntime = m.runtime ?? '';
		formCoverImage = m.cover_image ?? '';
		formTmdbId = m.tmdb_id;
		tmdbQuery = '';
		tmdbResults = [];
		modalError = '';
		showModal = true;
	}

	function closeModal() {
		showModal = false;
		editMovie = null;
		deleteTarget = null;
	}

	// ── TMDB search inside modal ──────────────────────────────────────────────
	async function handleTmdbSearch(e: Event) {
		e.preventDefault();
		if (!tmdbQuery.trim()) return;
		tmdbSearching = true;
		try {
			const res = await searchTmdb(tmdbQuery.trim());
			tmdbResults = res.results ?? [];
		} catch {
			tmdbResults = [];
		} finally {
			tmdbSearching = false;
		}
	}

	async function applyTmdbResult(t: TmdbMovie) {
		formTitle = t.title;
		const year = t.release_date?.split('-')[0];
		if (year) formYear = Number(year);
		if (t.poster_path) {
			formCoverImage = `https://image.tmdb.org/t/p/w500${t.poster_path}`;
		}
		formTmdbId = t.id;
		tmdbResults = [];
		tmdbQuery = '';

		// Fetch full details to pre-populate runtime and genres
		try {
			const details = await getTmdbMovie(t.id);
			if (details.runtime) formRuntime = details.runtime;
			if (details.genre_names?.length) formGenre = details.genre_names.join(', ');
			if (details.poster_url && !formCoverImage) formCoverImage = details.poster_url;
		} catch {
			// Non-critical — fields can be filled manually or enriched after save
		}
	}

	// ── Save / delete ─────────────────────────────────────────────────────────
	async function handleSave(e: Event) {
		e.preventDefault();
		modalError = '';

		if (!formStorageId) {
			modalError = 'Please select a storage location';
			return;
		}

		modalLoading = true;
		try {
			const payload: MovieCreate = {
				title: formTitle.trim(),
				year: Number(formYear),
				format: formFormat,
				storage_id: formStorageId,
				tmdb_id: formTmdbId,
				genre: formGenre ? formGenre.split(',').map((g) => g.trim()).filter(Boolean) : undefined,
				runtime: formRuntime !== '' ? Number(formRuntime) : undefined,
				cover_image: formCoverImage.trim() || undefined
			};

			if (editMovie) {
				await updateMovie(editMovie.id, payload);
			} else {
				await createMovie(payload);
			}
			const wasEdit = !!editMovie;
			closeModal();
			toast.success(wasEdit ? 'Movie updated' : 'Movie added');
			await loadMovies();
		} catch (err) {
			modalError = err instanceof ApiError ? err.message : 'Failed to save movie';
		} finally {
			modalLoading = false;
		}
	}

	async function handleDelete() {
		if (!deleteTarget) return;
		modalLoading = true;
		try {
			await deleteMovie(deleteTarget.id);
			toast.success('Movie deleted');
			deleteTarget = null;
			await loadMovies();
		} catch (err) {
			toast.error(err instanceof ApiError ? err.message : 'Failed to delete movie');
			deleteTarget = null;
		} finally {
			modalLoading = false;
		}
	}

	async function handleEnrich(m: Movie) {
		try {
			await enrichMovie(m.id);
			toast.success('Metadata fetched from TMDB');
			await loadMovies();
		} catch {
			toast.error('TMDB enrichment failed — check your API key');
		}
	}

	function formatRuntime(minutes: number): string {
		if (minutes < 60) return `${minutes}m`;
		const h = Math.floor(minutes / 60);
		const m = minutes % 60;
		return m > 0 ? `${h}h ${m}m` : `${h}h`;
	}

	// ── Filter apply ──────────────────────────────────────────────────────────
	function applyFilters() {
		goto(`/movies${searchQuery ? `?q=${encodeURIComponent(searchQuery)}` : ''}`);
		loadMovies();
	}

	function clearFilters() {
		filterFormat = '';
		filterStorage = '';
		filterGenre = '';
		searchQuery = '';
		goto('/movies');
		loadMovies();
	}
</script>

<div class="p-6">
	<!-- Page header -->
	<div class="flex items-center justify-between mb-6">
		<div>
			<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-50">Movies</h2>
			<p class="text-sm text-surface-500 mt-0.5">{movies.length} title{movies.length !== 1 ? 's' : ''}</p>
		</div>
		<button
			onclick={openCreate}
			class="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-500 hover:bg-primary-600 text-white font-medium text-sm transition-colors"
		>
			<span>+</span> Add Movie
		</button>
	</div>

	<!-- Filters bar -->
	<div class="flex flex-wrap gap-3 mb-6 p-4 bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700">
		<select
			bind:value={filterFormat}
			onchange={applyFilters}
			class="text-sm px-3 py-1.5 rounded-lg border border-surface-200 dark:border-surface-600 bg-surface-50 dark:bg-surface-700 text-surface-700 dark:text-surface-300"
		>
			<option value="">All Formats</option>
			{#each FORMATS as f}
				<option value={f}>{f}</option>
			{/each}
		</select>

		<div class="flex flex-col gap-1">
			<select
				bind:value={filterStorage}
				onchange={applyFilters}
				class="text-sm px-3 py-1.5 rounded-lg border border-surface-200 dark:border-surface-600 bg-surface-50 dark:bg-surface-700 text-surface-700 dark:text-surface-300"
			>
				<option value="">All Storage</option>
				{#each storageOptions as { storage, depth }}
					<option value={storage.id}>
						{#if depth > 0}{' '.repeat(depth * 2)}└ {/if}{storage.name}
					</option>
				{/each}
			</select>
			{#if filterStorage && selectedStorageHasChildren && filterIncludeDescendants}
				<span class="text-xs text-primary-500 px-1">includes sub-locations</span>
			{/if}
		</div>

		<input
			type="text"
			bind:value={filterGenre}
			onchange={applyFilters}
			placeholder="Genre…"
			class="text-sm px-3 py-1.5 rounded-lg border border-surface-200 dark:border-surface-600 bg-surface-50 dark:bg-surface-700 text-surface-700 dark:text-surface-300 w-32"
		/>

		{#if filterFormat || filterStorage || filterGenre || searchQuery}
			<button
				onclick={clearFilters}
				class="text-sm px-3 py-1.5 rounded-lg text-error-600 dark:text-error-400 hover:bg-error-50 dark:hover:bg-error-950 transition-colors"
			>
				Clear filters
			</button>
		{/if}
	</div>

	<!-- Search result banner -->
	{#if searchQuery}
		<div class="mb-4 text-sm text-surface-500">
			Search results for <strong class="text-surface-700 dark:text-surface-300">"{searchQuery}"</strong>
		</div>
	{/if}

	<!-- Error -->
	{#if error}
		<div class="mb-4 p-3 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200 text-sm">
			{error}
		</div>
	{/if}

	<!-- Loading skeletons -->
	{#if loading}
		<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
			{#each Array(12) as _}
				<div class="bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 overflow-hidden animate-pulse">
					<div class="aspect-[2/3] bg-surface-200 dark:bg-surface-700"></div>
					<div class="p-2.5 space-y-2">
						<div class="h-3 bg-surface-200 dark:bg-surface-700 rounded w-4/5"></div>
						<div class="h-3 bg-surface-200 dark:bg-surface-700 rounded w-2/5"></div>
					</div>
				</div>
			{/each}
		</div>
	{:else if movies.length === 0}
		<div class="text-center py-20 text-surface-400">
			<p class="text-4xl mb-3">🎬</p>
			<p class="text-lg font-medium">No movies found</p>
			<p class="text-sm mt-1">
				{searchQuery ? 'Try a different search term' : 'Add your first movie to get started'}
			</p>
		</div>
	{:else}
		<!-- Movie grid -->
		<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
			{#each movies as movie (movie.id)}
				<div class="group relative bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 overflow-hidden hover:shadow-lg transition-shadow">
					<!-- Poster -->
					<div class="aspect-[2/3] bg-surface-100 dark:bg-surface-700 relative overflow-hidden">
						{#if movie.cover_image}
							<img
								src={movie.cover_image}
								alt={movie.title}
								class="w-full h-full object-cover"
								loading="lazy"
							/>
						{:else}
							<div class="w-full h-full flex items-center justify-center text-surface-400 text-4xl">
								🎬
							</div>
						{/if}

						<!-- Hover actions -->
						<div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
							<button
								onclick={() => openEdit(movie)}
								class="p-2 rounded-lg bg-white/20 hover:bg-white/30 text-white transition-colors text-sm"
								title="Edit"
							>
								✏️
							</button>
							<button
								onclick={() => (deleteTarget = movie)}
								class="p-2 rounded-lg bg-white/20 hover:bg-white/30 text-white transition-colors text-sm"
								title="Delete"
							>
								🗑️
							</button>
							{#if movie.tmdb_id}
								<button
									onclick={() => handleEnrich(movie)}
									class="p-2 rounded-lg bg-white/20 hover:bg-white/30 text-white transition-colors text-sm"
									title="Fetch TMDB metadata"
								>
									✨
								</button>
							{/if}
						</div>
					</div>

					<!-- Info -->
					<div class="p-2.5">
						<p class="text-xs font-semibold text-surface-900 dark:text-surface-50 line-clamp-2 leading-tight" title={movie.title}>
							{movie.title}
						</p>
						<p class="text-xs text-surface-400 mt-0.5">{movie.year}</p>
						<div class="flex items-center justify-between mt-1.5">
							<span class="text-xs px-1.5 py-0.5 rounded bg-surface-100 dark:bg-surface-700 text-surface-500 font-medium">
								{movie.format}
							</span>
							<span class="text-xs text-surface-400 truncate ml-1" title={storageName(movie.storage_id)}>
								{storageName(movie.storage_id)}
							</span>
						</div>
						{#if movie.runtime}
							<p class="text-xs text-surface-400 mt-1">{formatRuntime(movie.runtime)}</p>
						{/if}
						{#if movie.genre && movie.genre.length > 0}
							<div class="flex flex-wrap gap-1 mt-1.5">
								{#each movie.genre.slice(0, 2) as g}
									<span class="text-xs px-1.5 py-0.5 rounded-full bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300">
										{g}
									</span>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Add / Edit Modal -->
{#if showModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<!-- Backdrop -->
		<button class="absolute inset-0 bg-black/50 w-full" onclick={closeModal} aria-label="Close dialog"></button>

		<!-- Modal -->
		<div class="relative bg-white dark:bg-surface-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
			<div class="sticky top-0 bg-white dark:bg-surface-800 px-6 py-4 border-b border-surface-200 dark:border-surface-700 flex items-center justify-between">
				<h3 class="text-lg font-semibold text-surface-900 dark:text-surface-50">
					{editMovie ? 'Edit Movie' : 'Add Movie'}
				</h3>
				<button onclick={closeModal} class="text-surface-400 hover:text-surface-600 dark:hover:text-surface-200 text-xl leading-none">✕</button>
			</div>

			<div class="px-6 py-5 space-y-5">
				<!-- TMDB Search -->
				<div>
					<p class="text-xs font-medium text-surface-500 uppercase tracking-wide mb-2">Quick fill from TMDB</p>
					<form onsubmit={handleTmdbSearch} class="flex gap-2">
						<input
							type="text"
							bind:value={tmdbQuery}
							placeholder="Search TMDB for a title…"
							class="flex-1 text-sm px-3 py-2 rounded-lg border border-surface-200 dark:border-surface-600 bg-surface-50 dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
						/>
						<button
							type="submit"
							disabled={tmdbSearching}
							class="px-3 py-2 text-sm rounded-lg bg-surface-100 dark:bg-surface-700 hover:bg-surface-200 dark:hover:bg-surface-600 text-surface-700 dark:text-surface-300 transition-colors"
						>
							{tmdbSearching ? '…' : 'Search'}
						</button>
					</form>

					{#if tmdbResults.length > 0}
						<div class="mt-2 border border-surface-200 dark:border-surface-600 rounded-lg overflow-hidden max-h-48 overflow-y-auto">
							{#each tmdbResults as t}
								<button
									onclick={() => applyTmdbResult(t)}
									class="w-full text-left px-3 py-2 text-sm hover:bg-surface-50 dark:hover:bg-surface-700 flex items-center gap-3 border-b border-surface-100 dark:border-surface-700 last:border-0"
								>
									{#if t.poster_path}
										<img
											src={`https://image.tmdb.org/t/p/w45${t.poster_path}`}
											alt={t.title}
											class="w-8 h-12 object-cover rounded flex-shrink-0"
										/>
									{:else}
										<div class="w-8 h-12 bg-surface-200 dark:bg-surface-600 rounded flex-shrink-0 flex items-center justify-center text-xs">?</div>
									{/if}
									<div>
										<p class="font-medium text-surface-900 dark:text-surface-50">{t.title}</p>
										<p class="text-xs text-surface-400">{t.release_date?.split('-')[0] ?? ''}</p>
									</div>
								</button>
							{/each}
						</div>
					{/if}
				</div>

				<hr class="border-surface-200 dark:border-surface-700" />

				{#if modalError}
					<div class="p-3 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200 text-sm">
						{modalError}
					</div>
				{/if}

				<form id="movie-form" onsubmit={handleSave} class="space-y-4">
					<div class="grid grid-cols-2 gap-4">
						<div class="col-span-2">
							<label for="form-title" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
								Title <span class="text-error-500">*</span>
							</label>
							<input
								id="form-title"
								type="text"
								bind:value={formTitle}
								required
								class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
								placeholder="Movie title"
							/>
						</div>

						<div>
							<label for="form-year" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
								Year <span class="text-error-500">*</span>
							</label>
							<input
								id="form-year"
								type="number"
								bind:value={formYear}
								required
								min="1888"
								max={new Date().getFullYear() + 2}
								class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
							/>
						</div>

						<div>
							<label for="form-format" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
								Format <span class="text-error-500">*</span>
							</label>
							<select
								id="form-format"
								bind:value={formFormat}
								class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
							>
								{#each FORMATS as f}
									<option value={f}>{f}</option>
								{/each}
							</select>
						</div>

						<div class="col-span-2">
							<label for="form-storage" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
								Storage Location <span class="text-error-500">*</span>
							</label>
							<select
								id="form-storage"
								bind:value={formStorageId}
								required
								class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
							>
								<option value="">Select storage…</option>
								{#each storageList as s}
									<option value={s.id}>{s.name} ({s.type})</option>
								{/each}
							</select>
						</div>

						<div>
							<label for="form-runtime" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
								Runtime (min)
							</label>
							<input
								id="form-runtime"
								type="number"
								bind:value={formRuntime}
								min="1"
								class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
								placeholder="e.g. 120"
							/>
						</div>

						<div>
							<label for="form-genre" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
								Genres
							</label>
							<input
								id="form-genre"
								type="text"
								bind:value={formGenre}
								class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
								placeholder="Action, Drama, …"
							/>
						</div>

						<div class="col-span-2">
							<label for="form-cover" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
								Cover Image URL
							</label>
							<input
								id="form-cover"
								type="url"
								bind:value={formCoverImage}
								class="w-full px-3 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
								placeholder="https://…"
							/>
						</div>
					</div>
				</form>
			</div>

			<div class="px-6 py-4 border-t border-surface-200 dark:border-surface-700 flex justify-end gap-3">
				<button onclick={closeModal} class="px-4 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-700 transition-colors">
					Cancel
				</button>
				<button
					form="movie-form"
					type="submit"
					disabled={modalLoading}
					class="px-4 py-2 text-sm rounded-lg bg-primary-500 hover:bg-primary-600 disabled:opacity-50 text-white font-medium transition-colors"
				>
					{modalLoading ? 'Saving…' : editMovie ? 'Save Changes' : 'Add Movie'}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Delete confirmation -->
{#if deleteTarget}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<button class="absolute inset-0 bg-black/50 w-full" onclick={() => (deleteTarget = null)} aria-label="Close dialog"></button>
		<div class="relative bg-white dark:bg-surface-800 rounded-2xl shadow-2xl w-full max-w-sm p-6">
			<h3 class="text-lg font-semibold text-surface-900 dark:text-surface-50 mb-2">Delete Movie</h3>
			<p class="text-sm text-surface-600 dark:text-surface-400 mb-6">
				Are you sure you want to delete <strong>{deleteTarget.title}</strong>? This cannot be undone.
			</p>
			<div class="flex justify-end gap-3">
				<button
					onclick={() => (deleteTarget = null)}
					class="px-4 py-2 text-sm rounded-lg border border-surface-200 dark:border-surface-600 text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-700 transition-colors"
				>
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
