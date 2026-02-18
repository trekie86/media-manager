<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { auth } from '$lib/stores/auth';
	import { login } from '$lib/api/auth';
	import { getMe } from '$lib/api/auth';
	import { ApiError } from '$lib/api/client';
	import { onMount } from 'svelte';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		auth.init();
		if (auth.isAuthenticated()) goto('/movies');
	});

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const token = await login(username, password);
			auth.login(token.access_token, { username });
			// Fetch full user profile
			const user = await getMe();
			auth.setUser({ username: user.username });
			const redirect = $page.url.searchParams.get('redirect') || '/movies';
			goto(redirect);
		} catch (err) {
			if (err instanceof ApiError) {
				error = err.message;
			} else {
				error = 'Login failed. Please try again.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-surface-100 dark:bg-surface-900 px-4">
	<div class="w-full max-w-md">
		<!-- Header -->
		<div class="text-center mb-8">
			<h1 class="text-3xl font-bold text-surface-900 dark:text-surface-50">Media Manager</h1>
			<p class="mt-2 text-surface-500">Sign in to your collection</p>
		</div>

		<!-- Card -->
		<div class="bg-white dark:bg-surface-800 rounded-2xl shadow-xl p-8">
			<h2 class="text-xl font-semibold mb-6 text-surface-800 dark:text-surface-100">Sign In</h2>

			{#if error}
				<div class="mb-4 p-3 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200 text-sm">
					{error}
				</div>
			{/if}

			<form onsubmit={handleSubmit} class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1" for="username">
						Username
					</label>
					<input
						id="username"
						type="text"
						bind:value={username}
						required
						autocomplete="username"
						class="w-full px-3 py-2 rounded-lg border border-surface-300 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
						placeholder="Enter username"
					/>
				</div>

				<div>
					<label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1" for="password">
						Password
					</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						required
						autocomplete="current-password"
						class="w-full px-3 py-2 rounded-lg border border-surface-300 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-900 dark:text-surface-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
						placeholder="Enter password"
					/>
				</div>

				<button
					type="submit"
					disabled={loading}
					class="w-full py-2.5 px-4 rounded-lg bg-primary-500 hover:bg-primary-600 disabled:opacity-50 text-white font-medium transition-colors"
				>
					{loading ? 'Signing in…' : 'Sign In'}
				</button>
			</form>

			<p class="mt-6 text-center text-sm text-surface-500">
				Don't have an account?
				<a href="/register" class="text-primary-500 hover:text-primary-600 font-medium">Register</a>
			</p>
		</div>
	</div>
</div>
