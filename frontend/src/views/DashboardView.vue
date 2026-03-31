<template>
  <div class="grid">
    <section class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Overview</p>
          <h2>值班总览</h2>
        </div>
        <el-tag type="danger">{{ overview?.current_risk_level ?? "-" }}</el-tag>
      </div>
      <div class="grid cards">
        <div class="card-stat">
          <div class="label">今日异常数</div>
          <div class="value">{{ overview?.today_anomaly_count ?? 0 }}</div>
        </div>
        <div class="card-stat">
          <div class="label">视频状态</div>
          <div class="value">{{ overview?.modality_health?.video ?? "-" }}</div>
        </div>
        <div class="card-stat">
          <div class="label">指标通道</div>
          <div class="value">{{ overview?.modality_health?.metrics ?? "-" }}</div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>重点告警</h3>
      </div>
      <el-table :data="overview?.key_alerts ?? []" style="width: 100%">
        <el-table-column prop="title" label="事件" />
        <el-table-column prop="severity" label="级别" />
        <el-table-column prop="time" label="时间" />
      </el-table>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>处置建议</h3>
      </div>
      <div class="timeline">
        <div v-for="item in overview?.advice_cards ?? []" :key="item.advice_key" class="timeline-item">
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

const overview = ref<any>();

onMounted(async () => {
  const { data } = await api.get("/overview");
  overview.value = data;
});
</script>

