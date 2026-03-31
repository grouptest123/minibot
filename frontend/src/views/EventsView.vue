<template>
  <div class="grid">
    <section class="panel">
      <div class="section-title">
        <h2>事件详情</h2>
      </div>
      <el-table :data="events" @row-click="selectEvent" style="width: 100%">
        <el-table-column prop="event_id" label="事件 ID" width="120" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="occurred_at" label="时间" width="180" />
      </el-table>
    </section>

    <section v-if="selected" class="panel">
      <div class="section-title">
        <h3>{{ selected.title }}</h3>
        <el-tag>{{ selected.anomaly.severity }}</el-tag>
      </div>
      <p>{{ selected.anomaly.summary }}</p>
      <h4>多模态证据</h4>
      <div class="timeline">
        <div v-for="item in selected.observation.evidences" :key="item.source + item.timestamp" class="timeline-item">
          <strong>{{ item.source }}</strong>
          <p>{{ item.summary }}</p>
          <small>{{ item.timestamp }}</small>
        </div>
      </div>
      <h4>建议列表</h4>
      <div class="timeline">
        <div v-for="item in selected.advices" :key="item.advice_key" class="timeline-item">
          <strong>{{ item.action }}</strong>
          <p>{{ item.rationale }}</p>
          <small>{{ item.evidence_summary }}</small>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api";

const events = ref<any[]>([]);
const selected = ref<any>();

async function loadEvents() {
  const { data } = await api.get("/events");
  events.value = data;
  selected.value = data[0];
}

function selectEvent(row: any) {
  selected.value = row;
}

onMounted(loadEvents);
</script>

