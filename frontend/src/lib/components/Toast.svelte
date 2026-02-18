<script lang="ts">
	import { toast } from '$lib/stores/toast';

	const ICONS = { success: '✓', error: '✕', info: 'ℹ' };
	const COLORS = {
		success: 'bg-green-600',
		error: 'bg-red-600',
		info: 'bg-blue-600'
	};
</script>

<div
	aria-live="polite"
	aria-atomic="false"
	class="fixed bottom-5 right-5 z-[200] flex flex-col gap-2 pointer-events-none"
>
	{#each $toast as t (t.id)}
		<div
			role="status"
			class="flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg text-white text-sm font-medium pointer-events-auto {COLORS[t.type]}"
			style="min-width: 15rem; max-width: 24rem;"
		>
			<span class="flex-shrink-0 w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-xs font-bold">
				{ICONS[t.type]}
			</span>
			<span class="flex-1">{t.message}</span>
			<button
				onclick={() => toast.remove(t.id)}
				class="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity text-xs leading-none"
				aria-label="Dismiss"
			>
				✕
			</button>
		</div>
	{/each}
</div>
