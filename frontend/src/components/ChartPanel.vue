<template>
  <div ref="container" class="chart-panel" :style="{ height: props.height ?? '300px' }"></div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";

const props = defineProps<{
  option: Record<string, any>;
  height?: string;
}>();

const container = ref<HTMLElement | null>(null);
let chart: echarts.ECharts | null = null;

function render() {
  if (!container.value) return;
  if (!chart) {
    chart = echarts.init(container.value);
  }
  chart.setOption(props.option, true);
  chart.resize();
}

onMounted(async () => {
  await nextTick();
  render();
  window.addEventListener("resize", render);
});

watch(
  () => props.option,
  async () => {
    await nextTick();
    render();
  },
  { deep: true }
);

onBeforeUnmount(() => {
  window.removeEventListener("resize", render);
  chart?.dispose();
});
</script>

<style scoped>
.chart-panel {
  width: 100%;
  min-height: 260px;
}
</style>
