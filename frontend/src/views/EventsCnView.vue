<template>
  <div class="events-grid">
    <section class="panel">
      <div class="section-title">
        <h3>事件工作台</h3>
      </div>
      <el-table :data="events" @row-click="selectEvent" style="width: 100%">
        <el-table-column prop="event_id" label="事件 ID" width="120" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="occurred_at" label="时间" width="180" />
      </el-table>
    </section>

    <template v-if="selected">
      <section class="panel event-hero hero-board">
        <div class="hero-main">
          <h2>{{ selected.title }}</h2>
          <p class="hero-subtitle">{{ selected.anomaly.summary }}</p>
        </div>
        <div class="hero-metrics compact-metrics">
          <div class="hero-metric hero-metric-danger">
            <span>严重度</span>
            <strong>{{ severityLabel(selected.anomaly.severity) }}</strong>
            <small>{{ selected.anomaly.category }}</small>
          </div>
          <div class="hero-metric">
            <span>风险趋势</span>
            <strong>{{ trendLabel(selected.anomaly.trend) }}</strong>
            <small>{{ selected.observation.risk_level }}</small>
          </div>
          <div class="hero-metric">
            <span>置信度</span>
            <strong>{{ Math.round(Number(selected.ai_insight.confidence) * 100) }}%</strong>
            <small>智能研判</small>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h3>研判流程</h3>
        </div>
        <div class="stage-flow wide">
          <div v-for="step in selected.ai_insight.process_flow ?? []" :key="step.stage" class="stage-card">
            <span>{{ step.stage }}</span>
            <strong>{{ step.status }}</strong>
            <small>{{ step.detail }}</small>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h3>多模态融合时间轴</h3>
        </div>
        <div class="fusion-board">
          <div v-for="item in selected.ai_insight.fusion_timeline ?? []" :key="item.time + item.source + item.label" class="fusion-event">
            <div class="fusion-time">{{ item.time }}</div>
            <div class="fusion-content">
              <strong>{{ item.source }}</strong>
              <p>{{ item.label }}</p>
              <small>风险窗口：{{ item.risk }}</small>
            </div>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h3>信号强度</h3>
        </div>
        <div class="signal-stack">
          <div v-for="item in selected.ai_insight.signal_strength ?? []" :key="item.name" class="signal-row">
            <span>{{ item.name }}</span>
            <div class="signal-bar">
              <div class="signal-fill" :style="{ width: `${Number(item.value) * 100}%` }"></div>
            </div>
            <strong>{{ Math.round(Number(item.value) * 100) }}%</strong>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h3>问题关键帧</h3>
        </div>
        <div class="keyframe-grid">
          <div v-for="item in selected.video_summary.timeline ?? []" :key="`${item.timestamp}-${item.image_url}`" class="keyframe-card">
            <img v-if="item.image_url" :src="item.image_url" :alt="item.status" />
            <div v-else class="frame-placeholder">暂无关键帧</div>
            <strong>{{ item.status }}</strong>
            <p>{{ item.note }}</p>
            <small>{{ item.timestamp }} / {{ item.source_mode }}</small>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h3>知识与案例命中</h3>
        </div>
        <div class="insight-grid">
          <article v-for="item in selected.ai_insight.knowledge_hits ?? []" :key="`kb-${item.title}`" class="insight-card">
            <div class="insight-head">
              <strong>{{ item.title }}</strong>
              <span>{{ item.score }}</span>
            </div>
            <p>{{ item.snippet }}</p>
          </article>
          <article v-for="item in selected.ai_insight.case_hits ?? []" :key="`case-${item.title}`" class="insight-card">
            <div class="insight-head">
              <strong>{{ item.title }}</strong>
              <span>{{ item.score }}</span>
            </div>
            <p>{{ item.snippet }}</p>
          </article>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h3>处置建议</h3>
        </div>
        <div class="pipeline-grid">
          <div v-for="item in selected.advices" :key="item.advice_key" class="pipeline-card" data-tone="accent">
            <small>{{ adviceLevelLabel(item.level) }}</small>
            <strong>{{ item.action }}</strong>
            <p>{{ item.rationale }}</p>
          </div>
        </div>
      </section>
    </template>
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

function severityLabel(value: string) {
  const mapping: Record<string, string> = {
    critical: "严重",
    high: "高",
    medium: "中",
    low: "低",
  };
  return mapping[value] ?? value;
}

function trendLabel(value: string) {
  const mapping: Record<string, string> = {
    risk_up: "上升",
    stable: "平稳",
    risk_down: "下降",
  };
  return mapping[value] ?? value;
}

function adviceLevelLabel(value: string) {
  const mapping: Record<string, string> = {
    observe: "观察",
    investigate: "排查",
    escalate: "上报",
    urgent_action: "紧急处置",
  };
  return mapping[value] ?? value;
}

onMounted(loadEvents);
</script>
