<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { auth } from '$lib/stores/auth';
	import { getMe } from '$lib/api/auth';

	let error = $state('');

	onMount(async () => {
		const token = $page.url.searchParams.get('token');
		const errorParam = $page.url.searchParams.get('error');

		if (errorParam) {
			error = 'Authentication failed. Please try again.';
			return;
		}

		if (!token) {
			goto('/login');
			return;
		}

		// Store token immediately so getMe() can use the Authorization header
		auth.login(token, null);

		try {
			const user = await getMe();
			auth.setUser(user);

			if (user.status === 'pending') {
				goto('/pending-approval');
			} else {
				goto('/movies');
			}
		} catch {
			auth.logout();
			goto('/login');
		}
	});
</script>

{#if error}
	<div class="min-h-screen flex items-center justify-center">
		<p class="text-error-600">{error}</p>
	</div>
{:else}
	<div class="min-h-screen flex items-center justify-center">
		<p class="text-surface-500">Completing sign in…</p>
	</div>
{/if}
