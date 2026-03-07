<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import { listPendingUsers, approveUser, rejectUser, type PendingUser } from '$lib/api/auth';

	let pendingUsers = $state<PendingUser[]>([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		if (!auth.isAdmin()) {
			goto('/movies');
			return;
		}
		await loadPendingUsers();
	});

	async function loadPendingUsers() {
		loading = true;
		error = '';
		try {
			pendingUsers = await listPendingUsers();
		} catch {
			error = 'Failed to load pending users.';
		} finally {
			loading = false;
		}
	}

	async function handleApprove(userId: string) {
		try {
			await approveUser(userId);
			pendingUsers = pendingUsers.filter((u) => u.id !== userId);
		} catch {
			error = 'Failed to approve user.';
		}
	}

	async function handleReject(userId: string) {
		try {
			await rejectUser(userId);
			pendingUsers = pendingUsers.filter((u) => u.id !== userId);
		} catch {
			error = 'Failed to reject user.';
		}
	}
</script>

<div class="p-6 max-w-3xl mx-auto">
	<h1 class="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-6">User Approvals</h1>

	{#if error}
		<div class="mb-4 p-3 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200 text-sm">
			{error}
		</div>
	{/if}

	{#if loading}
		<p class="text-surface-500">Loading…</p>
	{:else if pendingUsers.length === 0}
		<div class="text-center py-12 text-surface-400">
			<p class="text-lg">No pending users</p>
			<p class="text-sm mt-1">All users have been reviewed.</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each pendingUsers as user (user.id)}
				<div class="bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 p-4 flex items-center justify-between gap-4">
					<div class="min-w-0">
						<p class="font-medium text-surface-900 dark:text-surface-50 truncate">{user.display_name}</p>
						<p class="text-sm text-surface-500 truncate">{user.email}</p>
						<p class="text-xs text-surface-400 mt-0.5">via {user.provider}</p>
					</div>
					<div class="flex gap-2 flex-shrink-0">
						<button
							onclick={() => handleApprove(user.id)}
							class="px-3 py-1.5 text-sm rounded-lg bg-success-500 hover:bg-success-600 text-white font-medium transition-colors"
						>
							Approve
						</button>
						<button
							onclick={() => handleReject(user.id)}
							class="px-3 py-1.5 text-sm rounded-lg bg-error-500 hover:bg-error-600 text-white font-medium transition-colors"
						>
							Reject
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
