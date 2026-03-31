<template>
  <div class="grid">
    <section class="panel hero-panel">
      <div class="hero-copy">
        <p class="eyebrow">Agentic Workflow</p>
        <h2>值班机器人正在持续感知、融合和研判</h2>
        <p class="hero-subtitle">
          当前页面不仅展示结果，还显示了 AI 从多源感知到决策输出的处理过程，让 Demo 更像一个正在工作的智能系统。
        </p>
      </div>
      <div class="process-strip">
        <div v-for="item in overview?.process_board ?? []" :key="item.title" class="process-card" :data-tone="item.tone">
          <span class="process-step">{{ item.title }}</span>
          <strong>{{ item.metric }}</strong>
          <small>{{ item.detail }}</small>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">AI Duty Center</p>
          <h2>智能值班总览</h2>
        </div>
        <el-tag type="danger">{{ overview?.current_risk_level ?? "-" }}</el-tag>
      </div>
      <div class="grid cards">
        <div class="card-stat">
          <div class="label">今日异常数</div>
          <div class="value">{{ overview?.today_anomaly_count ?? 0 }}</div>
        </div>
        <div class="card-stat">
          <div class="label">视频风险</div>
          <div class="value">{{ overview?.video_digest?.risk_level ?? "-" }}</div>
        </div>
        <div class="card-stat">
          <div class="label">离岗次数</div>
          <div class="value">{{ overview?.video_digest?.absence_count ?? 0 }}</div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>AI 研判高亮</h3>
      </div>
      <div class="timeline signal-grid">
        <div v-for="item in overview?.ai_highlights ?? []" :key="item.title + item.judgement" class="timeline-item">
          <strong>{{ item.title }}</strong>
          <p>研判结论：{{ item.judgement }}</p>
          <p>原因假设：{{ item.hypothesis }}</p>
          <div class="confidence-row">
            <span>置信度</span>
            <div class="confidence-bar">
              <div class="confidence-fill" :style="{ width: `${Number(item.confidence) * 100}%` }"></div>
            </div>
            <span>{{ Math.round(Number(item.confidence) * 100) }}%</span>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>视频检测摘要</h3>
      </div>
      <div class="timeline">
        <div class="timeline-item">
          <strong>{{ overview?.video_digest?.summary }}</strong>
          <p>视频来源：{{ overview?.video_digest?.source_mode }} / {{ overview?.video_digest?.source }}</p>
          <p>最新状态：{{ overview?.video_digest?.latest_status }}</p>
          <p>分析方法：{{ (overview?.video_digest?.analysis_method ?? []).join(" / ") }}</p>
          <p>检测提示：{{ overview?.video_digest?.watch_area_hint }}</p>
          <small>平均置信度：{{ overview?.video_digest?.average_confidence }}</small>
        </div>
        <div class="mini-timeline">
          <div v-for="item in overview?.video_digest?.timeline ?? []" :key="item.timestamp" class="mini-node">
            <span>{{ item.timestamp.slice(11, 16) }}</span>
            <strong>{{ item.status }}</strong>
            <small>{{ item.note }}</small>
          </div>
        </div>
        <div v-if="overview?.video_digest?.timeline?.some((item: any) => item.image_url)" class="keyframe-grid">
          <div v-for="item in overview?.video_digest?.timeline ?? []" :key="`${item.timestamp}-${item.image_url}`" class="keyframe-card">
            <img v-if="item.image_url" :src="item.image_url" :alt="item.status" />
            <strong>{{ item.status }}</strong>
            <small>{{ item.timestamp }}</small>
          </div>
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
        <h3>系统处理轨迹</h3>
      </div>
      <div class="workflow-ladder">
        <div class="workflow-node">
          <span>01</span>
          <strong>采集输入</strong>
          <p>视频、日志、指标、截图、告警进入统一窗口</p>
        </div>
        <div class="workflow-node">
          <span>02</span>
          <strong>信号融合</strong>
          <p>按分钟级时间对齐并提取风险特征</p>
        </div>
        <div class="workflow-node">
          <span>03</span>
          <strong>检索知识</strong>
          <p>调用本地知识库和历史案例进行增强解释</p>
        </div>
        <div class="workflow-node">
          <span>04</span>
          <strong>输出建议</strong>
          <p>按风险等级与证据链生成处置动作</p>
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
