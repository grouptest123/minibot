<template>
  <div class="dashboard-grid">
    <section class="hero-board">
      <div class="hero-main">
        <p class="eyebrow">Agentic Command</p>
        <h2>机器人正在持续采集、融合并生成值班建议</h2>
        <p class="hero-subtitle">
          当前界面聚焦“信息融合 -> 异常识别 -> 处置建议 -> 信息生成”的完整链路，用更接近产品化中控台的方式呈现智能过程。
        </p>
      </div>
      <div class="hero-metrics">
        <div class="hero-metric hero-metric-danger">
          <span>总体风险</span>
          <strong>{{ overview?.current_risk_level ?? "-" }}</strong>
          <small>实时判定</small>
        </div>
        <div class="hero-metric">
          <span>今日异常</span>
          <strong>{{ overview?.today_anomaly_count ?? 0 }}</strong>
          <small>闭环事件</small>
        </div>
        <div class="hero-metric">
          <span>视频离岗</span>
          <strong>{{ overview?.video_digest?.absence_count ?? 0 }}</strong>
          <small>自动检测</small>
        </div>
      </div>
    </section>

    <section class="panel process-panel">
      <div class="section-title">
        <h3>智能处理流水线</h3>
        <span class="section-caption">Agentic Workflow</span>
      </div>
      <div class="pipeline-grid">
        <div v-for="item in overview?.process_board ?? []" :key="item.title" class="pipeline-card" :data-tone="item.tone">
          <small>{{ item.title }}</small>
          <strong>{{ item.metric }}</strong>
          <p>{{ item.detail }}</p>
        </div>
      </div>
    </section>

    <section class="panel risk-panel">
      <div class="section-title">
        <h3>风险信号面板</h3>
        <span class="section-caption">Signal Console</span>
      </div>
      <div class="stat-band">
        <div class="signal-stat">
          <span>视频风险</span>
          <strong>{{ overview?.video_digest?.risk_level ?? "-" }}</strong>
        </div>
        <div class="signal-stat">
          <span>最新状态</span>
          <strong>{{ overview?.video_digest?.latest_status ?? "-" }}</strong>
        </div>
        <div class="signal-stat">
          <span>平均置信度</span>
          <strong>{{ Math.round(Number(overview?.video_digest?.average_confidence ?? 0) * 100) }}%</strong>
        </div>
      </div>
      <div class="mini-timeline">
        <div v-for="item in overview?.video_digest?.timeline ?? []" :key="item.timestamp" class="mini-node">
          <span>{{ item.timestamp.slice(11, 16) }}</span>
          <strong>{{ item.status }}</strong>
          <small>{{ item.note }}</small>
        </div>
      </div>
    </section>

    <section class="panel insight-panel">
      <div class="section-title">
        <h3>AI 研判高亮</h3>
        <span class="section-caption">Reasoning Highlights</span>
      </div>
      <div class="insight-grid">
        <article v-for="item in overview?.ai_highlights ?? []" :key="item.title + item.judgement" class="insight-card">
          <div class="insight-head">
            <strong>{{ item.title }}</strong>
            <span>{{ Math.round(Number(item.confidence) * 100) }}%</span>
          </div>
          <p>结论：{{ item.judgement }}</p>
          <p>原因假设：{{ item.hypothesis }}</p>
          <div class="confidence-bar">
            <div class="confidence-fill" :style="{ width: `${Number(item.confidence) * 100}%` }"></div>
          </div>
        </article>
      </div>
    </section>

    <section class="panel visual-panel">
      <div class="section-title">
        <h3>视频异常追溯</h3>
        <span class="section-caption">Traceback Frames</span>
      </div>
      <div class="visual-summary-card">
        <div>
          <strong>{{ overview?.video_digest?.summary }}</strong>
          <p>来源：{{ overview?.video_digest?.source_mode }} / {{ overview?.video_digest?.source }}</p>
          <p>方法：{{ (overview?.video_digest?.analysis_method ?? []).join(" / ") }}</p>
          <small>{{ overview?.video_digest?.watch_area_hint }}</small>
        </div>
      </div>
      <div class="keyframe-grid">
        <div v-for="item in overview?.video_digest?.timeline ?? []" :key="`${item.timestamp}-${item.image_url}`" class="keyframe-card">
          <img v-if="item.image_url" :src="item.image_url" :alt="item.status" />
          <div v-else class="frame-placeholder">等待真实视频关键帧</div>
          <strong>{{ item.status }}</strong>
          <small>{{ item.timestamp }}</small>
        </div>
      </div>
    </section>

    <section class="panel alert-panel">
      <div class="section-title">
        <h3>重点告警</h3>
        <span class="section-caption">Critical Focus</span>
      </div>
      <el-table :data="overview?.key_alerts ?? []" style="width: 100%">
        <el-table-column prop="title" label="事件" />
        <el-table-column prop="severity" label="级别" />
        <el-table-column prop="time" label="时间" />
      </el-table>
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

