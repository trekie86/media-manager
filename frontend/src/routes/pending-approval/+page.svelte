<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { logout } from '$lib/api/auth';
	import { goto } from '$app/navigation';

	async function handleLogout() {
		try {
			await logout();
		} catch {
			// Ignore errors — clear client state regardless
		}
		auth.logout();
		goto('/login');
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-surface-100 dark:bg-surface-900 px-4">
	<div class="w-full max-w-md text-center">
		<div class="bg-white dark:bg-surface-800 rounded-2xl shadow-xl p-8">
			<div class="text-5xl mb-4">⏳</div>
			<h1 class="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-3">
				Account Pending Approval
			</h1>
			<p class="text-surface-500 mb-6">
				Your account has been created but needs to be approved by an admin before you can
				access the collection. Please check back later.
			</p>
			<button
				onclick={handleLogout}
				class="px-4 py-2 text-sm rounded-lg border border-surface-300 dark:border-surface-600 text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors"
			>
				Sign out
			</button>
		</div>
	</div>
</div>
