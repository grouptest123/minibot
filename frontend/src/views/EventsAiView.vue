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

      <h4>AI 研判</h4>
      <div class="timeline process-visual-grid">
        <div class="timeline-item emphasis-card">
          <strong>{{ selected.ai_insight.judgement }}</strong>
          <p>原因假设：{{ selected.ai_insight.hypothesis }}</p>
          <p>视频信号：{{ selected.ai_insight.video_signal?.latest_status }} / 风险 {{ selected.ai_insight.video_signal?.risk_level }}</p>
          <div class="confidence-row">
            <span>置信度</span>
            <div class="confidence-bar">
              <div class="confidence-fill" :style="{ width: `${Number(selected.ai_insight.confidence) * 100}%` }"></div>
            </div>
            <span>{{ Math.round(Number(selected.ai_insight.confidence) * 100) }}%</span>
          </div>
        </div>
        <div class="stage-flow">
          <div v-for="step in selected.ai_insight.process_flow ?? []" :key="step.stage" class="stage-card">
            <span>{{ step.stage }}</span>
            <strong>{{ step.status }}</strong>
            <small>{{ step.detail }}</small>
          </div>
        </div>
      </div>

      <h4>多模态融合时间轴</h4>
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

      <h4>信号强度</h4>
      <div class="signal-stack">
        <div v-for="item in selected.ai_insight.signal_strength ?? []" :key="item.name" class="signal-row">
          <span>{{ item.name }}</span>
          <div class="signal-bar">
            <div class="signal-fill" :style="{ width: `${Number(item.value) * 100}%` }"></div>
          </div>
          <strong>{{ Math.round(Number(item.value) * 100) }}%</strong>
        </div>
      </div>

      <h4>视频检测时间线</h4>
      <div class="timeline video-strip">
        <div v-for="item in selected.video_summary.timeline ?? []" :key="item.timestamp" class="timeline-item">
          <strong>{{ item.status }}</strong>
          <p>{{ item.note }}</p>
          <small>{{ item.timestamp }} / 置信度 {{ item.confidence }}</small>
        </div>
      </div>

      <h4>问题关键帧</h4>
      <div class="keyframe-grid">
        <div v-for="item in selected.video_summary.timeline ?? []" :key="`${item.timestamp}-${item.image_url}`" class="keyframe-card">
          <img v-if="item.image_url" :src="item.image_url" :alt="item.status" />
          <div v-else class="frame-placeholder">无关键帧</div>
          <strong>{{ item.status }}</strong>
          <p>{{ item.note }}</p>
          <small>{{ item.timestamp }} / {{ item.source_mode }}</small>
        </div>
      </div>

      <h4>多模态证据</h4>
      <div class="timeline">
        <div v-for="item in selected.observation.evidences" :key="item.source + item.timestamp" class="timeline-item">
          <strong>{{ item.source }}</strong>
          <p>{{ item.summary }}</p>
          <small>{{ item.timestamp }}</small>
        </div>
      </div>

      <h4>知识与案例命中</h4>
      <div class="timeline signal-grid">
        <div v-for="item in selected.ai_insight.knowledge_hits ?? []" :key="`kb-${item.title}`" class="timeline-item">
          <strong>{{ item.title }}</strong>
          <p>{{ item.snippet }}</p>
          <small>score={{ item.score }}</small>
        </div>
        <div v-for="item in selected.ai_insight.case_hits ?? []" :key="`case-${item.title}`" class="timeline-item">
          <strong>{{ item.title }}</strong>
          <p>{{ item.snippet }}</p>
          <small>score={{ item.score }}</small>
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

      <h4>工具调用轨迹</h4>
      <div class="workflow-ladder compact">
        <div class="workflow-node">
          <span>01</span>
          <strong>读取视频与指标</strong>
          <p>值守画面和运行指标被送入融合窗口</p>
        </div>
        <div class="workflow-node">
          <span>02</span>
          <strong>检索日志与告警</strong>
          <p>系统补充日志错误、告警级别和页面状态</p>
        </div>
        <div class="workflow-node">
          <span>03</span>
          <strong>命中知识与案例</strong>
          <p>检索本地预案和历史故障案例，形成解释依据</p>
        </div>
        <div class="workflow-node">
          <span>04</span>
          <strong>输出处置动作</strong>
          <p>基于证据强度和规则权重排序建议</p>
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
