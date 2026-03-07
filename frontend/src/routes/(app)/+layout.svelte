<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { auth } from '$lib/stores/auth';
	import { logout, getMe } from '$lib/api/auth';

	let { children } = $props();
	let searchQuery = $state('');
	let userMenuOpen = $state(false);

	onMount(async () => {
		auth.init();
		if (!auth.isAuthenticated()) {
			goto('/login');
			return;
		}
		// Load user profile if not already loaded
		if (!$auth.user) {
			try {
				const user = await getMe();
				auth.setUser(user);
			} catch {
				auth.logout();
				goto('/login');
			}
		}
	});

	async function handleLogout() {
		try {
			await logout();
		} catch {
			// Ignore logout errors - clear client state regardless
		}
		auth.logout();
		goto('/login');
	}

	function handleSearch(e: Event) {
		e.preventDefault();
		if (searchQuery.trim()) {
			goto(`/movies?q=${encodeURIComponent(searchQuery.trim())}`);
		}
	}

	const navItems = [
		{ href: '/movies', label: 'Movies', icon: '🎬' },
		{ href: '/storage', label: 'Storage', icon: '📦' }
	];
</script>

<div class="flex h-screen bg-surface-50 dark:bg-surface-950 overflow-hidden">
	<!-- Sidebar -->
	<aside class="w-60 flex-shrink-0 bg-surface-100 dark:bg-surface-900 border-r border-surface-200 dark:border-surface-700 flex flex-col">
		<!-- Logo -->
		<div class="px-5 py-5 border-b border-surface-200 dark:border-surface-700">
			<h1 class="text-lg font-bold text-surface-900 dark:text-surface-50">
				🎬 Media Manager
			</h1>
		</div>

		<!-- Navigation -->
		<nav class="flex-1 px-3 py-4 space-y-1">
			{#each navItems as item}
				<a
					href={item.href}
					class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
						{$page.url.pathname.startsWith(item.href)
							? 'bg-primary-500 text-white'
							: 'text-surface-700 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-800'}"
				>
					<span class="text-base">{item.icon}</span>
					{item.label}
				</a>
			{/each}

			{#if $auth.user?.role === 'admin'}
				<a
					href="/admin"
					class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
						{$page.url.pathname.startsWith('/admin')
							? 'bg-primary-500 text-white'
							: 'text-surface-700 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-800'}"
				>
					<span class="text-base">🔑</span>
					Admin
				</a>
			{/if}
		</nav>

		<!-- User section -->
		<div class="px-3 py-4 border-t border-surface-200 dark:border-surface-700">
			<div class="relative">
				<button
					onclick={() => (userMenuOpen = !userMenuOpen)}
					class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-surface-700 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-800 transition-colors"
				>
					{#if $auth.user?.avatar_url}
						<img
							src={$auth.user.avatar_url}
							alt="avatar"
							class="w-8 h-8 rounded-full flex-shrink-0 object-cover"
						/>
					{:else}
						<div class="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center text-white font-medium text-sm flex-shrink-0">
							{$auth.user?.display_name?.[0]?.toUpperCase() ?? '?'}
						</div>
					{/if}
					<span class="truncate">{$auth.user?.display_name ?? 'Loading…'}</span>
					<span class="ml-auto text-xs">▾</span>
				</button>

				{#if userMenuOpen}
					<div class="absolute bottom-full left-0 right-0 mb-1 bg-white dark:bg-surface-800 rounded-lg shadow-lg border border-surface-200 dark:border-surface-700 py-1 z-50">
						<button
							onclick={handleLogout}
							class="w-full text-left px-4 py-2 text-sm text-error-600 dark:text-error-400 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors"
						>
							Sign Out
						</button>
					</div>
				{/if}
			</div>
		</div>
	</aside>

	<!-- Main content -->
	<div class="flex-1 flex flex-col overflow-hidden">
		<!-- Top bar -->
		<header class="flex-shrink-0 h-14 bg-white dark:bg-surface-900 border-b border-surface-200 dark:border-surface-700 flex items-center px-5 gap-4">
			<form onsubmit={handleSearch} class="flex-1 max-w-md">
				<div class="relative">
					<span class="absolute left-3 top-1/2 -translate-y-1/2 text-surface-400">🔍</span>
					<input
						type="search"
						bind:value={searchQuery}
						placeholder="Search movies…"
						class="w-full pl-9 pr-4 py-1.5 text-sm rounded-lg border border-surface-200 dark:border-surface-600 bg-surface-50 dark:bg-surface-800 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
					/>
				</div>
			</form>
		</header>

		<!-- Page content -->
		<main class="flex-1 overflow-auto">
			{@render children()}
		</main>
	</div>
</div>

<!-- Click outside to close user menu -->
{#if userMenuOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div class="fixed inset-0 z-40" onclick={() => (userMenuOpen = false)}></div>
{/if}
