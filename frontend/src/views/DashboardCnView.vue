<template>
  <div class="dashboard-grid">
    <section class="hero-board">
      <div class="hero-main">
        <h2>态势总览</h2>
        <p class="hero-subtitle">围绕信息融合、异常识别、处置建议和信息生成的闭环态势面板。</p>
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
          <small>{{ overview?.video_digest?.source_mode ?? "待检测" }}</small>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>核心环节</h3>
      </div>
      <div class="interactive-grid">
        <button
          v-for="item in overview?.process_board ?? []"
          :key="item.title"
          type="button"
          class="interactive-card"
          :data-tone="item.tone"
          @click="openPanel(item.title)"
        >
          <small>{{ item.title }}</small>
          <strong>{{ item.metric }}</strong>
          <p>{{ item.detail }}</p>
          <span class="interactive-action">点击查看</span>
        </button>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>趋势与告警</h3>
      </div>
      <div class="overview-two-column">
        <div class="chart-card">
          <strong class="subheading">风险趋势</strong>
          <ChartPanel :option="trendOption" height="280px" />
        </div>
        <div class="table-card">
          <strong class="subheading">重点告警</strong>
          <el-table :data="overview?.key_alerts ?? []" style="width: 100%">
            <el-table-column prop="title" label="事件" />
            <el-table-column prop="severity" label="级别" width="100">
              <template #default="{ row }">
                {{ severityLabel(row.severity) }}
              </template>
            </el-table-column>
            <el-table-column prop="time" label="时间" width="180" />
          </el-table>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>视频风险与关键帧</h3>
      </div>
      <div class="overview-two-column">
        <div class="signal-panel">
          <div class="signal-stat-list">
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
              <span>{{ item.timestamp }}</span>
              <strong>{{ item.status }}</strong>
              <small>{{ item.note }}</small>
            </div>
          </div>
        </div>
        <div class="keyframe-grid compact-keyframe-grid">
          <div v-for="item in overview?.video_digest?.timeline ?? []" :key="`${item.timestamp}-${item.image_url}`" class="keyframe-card">
            <img v-if="item.image_url" :src="item.image_url" :alt="item.status" />
            <div v-else class="frame-placeholder">暂无关键帧</div>
            <strong>{{ item.status }}</strong>
            <p>{{ item.note }}</p>
            <small>{{ item.timestamp }}</small>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>智能研判与建议</h3>
      </div>
      <div class="overview-two-column">
        <div class="insight-grid">
          <article v-for="item in overview?.ai_highlights ?? []" :key="item.title + item.judgement" class="insight-card">
            <div class="insight-head">
              <strong>{{ item.title }}</strong>
              <span>{{ Math.round(Number(item.confidence) * 100) }}%</span>
            </div>
            <p>研判结论：{{ item.judgement }}</p>
            <p>原因假设：{{ item.hypothesis }}</p>
            <div class="confidence-bar">
              <div class="confidence-fill" :style="{ width: `${Number(item.confidence) * 100}%` }"></div>
            </div>
          </article>
        </div>
        <div class="pipeline-grid">
          <div v-for="item in overview?.advice_cards ?? []" :key="item.advice_key" class="pipeline-card" data-tone="accent">
            <small>{{ adviceLevelLabel(item.level) }}</small>
            <strong>{{ item.action }}</strong>
            <p>{{ item.evidence_summary }}</p>
          </div>
        </div>
      </div>
    </section>

    <el-dialog v-model="perceptionVisible" title="感知接入" width="78%" @opened="handlePerceptionOpened" @closed="stopCamera">
      <div class="dialog-block">
        <div class="stream-grid">
          <div v-for="stream in streamCards" :key="stream.stream_id" class="stream-card">
            <div class="stream-head">
              <strong>{{ stream.name }}</strong>
              <span>{{ stream.status }}</span>
            </div>
            <template v-if="stream.isCamera">
              <video
                :ref="bindCameraVideo"
                autoplay
                muted
                playsinline
                class="stream-video"
              ></video>
              <div v-if="cameraError" class="stream-error">{{ cameraError }}</div>
            </template>
            <video v-else-if="stream.url" :src="stream.url" controls muted loop playsinline class="stream-video"></video>
            <div v-else class="stream-placeholder">当前未接入样例视频，可将视频放入指定目录后重启服务。</div>
            <small>{{ stream.source }}</small>
          </div>
        </div>
        <div class="modality-grid">
          <div v-for="(status, name) in overview?.modality_health ?? {}" :key="name" class="modality-card">
            <span>{{ modalityLabel(name) }}</span>
            <strong>{{ modalityStatus(status) }}</strong>
          </div>
        </div>
        <div class="dialog-summary">
          <strong>当前演示采用 6 路接入示意</strong>
          <p>前 5 路为 mock 视频回放，用于模拟多路值班画面；第 6 路调用本机前置相机，展示真实接入效果。</p>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="videoVisible" title="视频检测结果" width="78%">
      <div class="dialog-block">
        <div class="dialog-summary">
          <strong>{{ overview?.video_digest?.summary }}</strong>
          <p>来源：{{ overview?.video_digest?.source_mode }} / {{ overview?.video_digest?.source }}</p>
          <p>方法：{{ (overview?.video_digest?.analysis_method ?? []).join("、") }}</p>
        </div>
        <div class="keyframe-grid">
          <div v-for="item in overview?.video_digest?.timeline ?? []" :key="`${item.timestamp}-${item.image_url}-dialog`" class="keyframe-card">
            <img v-if="item.image_url" :src="item.image_url" :alt="item.status" />
            <div v-else class="frame-placeholder">暂无关键帧</div>
            <strong>{{ item.status }}</strong>
            <p>{{ item.note }}</p>
            <small>{{ item.timestamp }}</small>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="decisionVisible" title="决策输出" width="82%">
      <div class="dialog-block">
        <div class="overview-two-column">
          <div class="chart-card">
            <strong class="subheading">处置信号雷达图</strong>
            <ChartPanel :option="decisionRadarOption" height="320px" />
          </div>
          <div class="chart-card">
            <strong class="subheading">风险变化线图</strong>
            <ChartPanel :option="decisionLineOption" height="320px" />
          </div>
        </div>
        <div class="decision-list">
          <div v-for="item in overview?.advice_cards ?? []" :key="`${item.advice_key}-decision`" class="decision-item">
            <div>
              <strong>{{ item.action }}</strong>
              <p>{{ item.rationale }}</p>
            </div>
            <span>{{ adviceLevelLabel(item.level) }}</span>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="fusionVisible" title="融合研判" width="78%">
      <div class="dialog-block">
        <div class="pipeline-grid">
          <div v-for="item in selectedEvent?.ai_insight?.process_flow ?? []" :key="item.stage" class="pipeline-card">
            <small>{{ item.stage }}</small>
            <strong>{{ item.status }}</strong>
            <p>{{ item.detail }}</p>
          </div>
        </div>
        <div class="insight-grid">
          <article v-for="item in selectedEvent?.ai_insight?.knowledge_hits ?? []" :key="`kb-${item.title}`" class="insight-card">
            <div class="insight-head">
              <strong>{{ item.title }}</strong>
              <span>{{ item.score }}</span>
            </div>
            <p>{{ item.snippet }}</p>
          </article>
          <article v-for="item in selectedEvent?.ai_insight?.case_hits ?? []" :key="`case-${item.title}`" class="insight-card">
            <div class="insight-head">
              <strong>{{ item.title }}</strong>
              <span>{{ item.score }}</span>
            </div>
            <p>{{ item.snippet }}</p>
          </article>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { api } from "../api";
import ChartPanel from "../components/ChartPanel.vue";

const overview = ref<any>();
const events = ref<any[]>([]);
const perceptionVisible = ref(false);
const videoVisible = ref(false);
const decisionVisible = ref(false);
const fusionVisible = ref(false);
const cameraVideo = ref<HTMLVideoElement | null>(null);
const cameraStream = ref<MediaStream | null>(null);
const cameraError = ref("");

const selectedEvent = computed(() => events.value[0]);
const mockVideoUrl = computed(() => {
  const source = overview.value?.video_digest?.source;
  const mode = overview.value?.video_digest?.source_mode;
  if (source && mode === "真实视频") {
    return `/input-video/${source}`;
  }
  return "";
});
const streamCards = computed(() => [
  {
    stream_id: "mock-1",
    name: "模拟视频 1",
    status: "模拟回放",
    source: mockVideoUrl.value ? "样例值班视频" : "未放入样例视频",
    url: mockVideoUrl.value,
    isCamera: false,
  },
  {
    stream_id: "mock-2",
    name: "模拟视频 2",
    status: "模拟回放",
    source: mockVideoUrl.value ? "样例值班视频" : "未放入样例视频",
    url: mockVideoUrl.value,
    isCamera: false,
  },
  {
    stream_id: "mock-3",
    name: "模拟视频 3",
    status: "模拟回放",
    source: mockVideoUrl.value ? "样例值班视频" : "未放入样例视频",
    url: mockVideoUrl.value,
    isCamera: false,
  },
  {
    stream_id: "mock-4",
    name: "模拟视频 4",
    status: "模拟回放",
    source: mockVideoUrl.value ? "样例值班视频" : "未放入样例视频",
    url: mockVideoUrl.value,
    isCamera: false,
  },
  {
    stream_id: "mock-5",
    name: "模拟视频 5",
    status: "模拟回放",
    source: mockVideoUrl.value ? "样例值班视频" : "未放入样例视频",
    url: mockVideoUrl.value,
    isCamera: false,
  },
  {
    stream_id: "camera-1",
    name: "本机前置相机",
    status: cameraStream.value ? "实时接入" : "待授权",
    source: "浏览器摄像头",
    url: "",
    isCamera: true,
  },
]);

const trendOption = computed(() => ({
  tooltip: { trigger: "axis" },
  grid: { left: 36, right: 20, top: 28, bottom: 28 },
  xAxis: {
    type: "category",
    boundaryGap: false,
    axisLabel: { color: "#9cb2c6" },
    data: (overview.value?.trend_points ?? []).map((item: any) => item.time),
  },
  yAxis: {
    type: "value",
    axisLabel: { color: "#9cb2c6" },
    splitLine: { lineStyle: { color: "rgba(151,176,196,0.12)" } },
  },
  series: [
    {
      name: "风险值",
      type: "line",
      smooth: true,
      areaStyle: { color: "rgba(45,212,191,0.12)" },
      lineStyle: { color: "#2dd4bf", width: 3 },
      itemStyle: { color: "#2dd4bf" },
      data: (overview.value?.trend_points ?? []).map((item: any) => item.risk),
    },
  ],
}));

const decisionLineOption = computed(() => ({
  tooltip: { trigger: "axis" },
  grid: { left: 40, right: 20, top: 28, bottom: 28 },
  xAxis: {
    type: "category",
    boundaryGap: false,
    axisLabel: { color: "#9cb2c6" },
    data: (overview.value?.trend_points ?? []).map((item: any) => item.time),
  },
  yAxis: {
    type: "value",
    axisLabel: { color: "#9cb2c6" },
    splitLine: { lineStyle: { color: "rgba(151,176,196,0.12)" } },
  },
  series: [
    {
      name: "异常数量",
      type: "line",
      smooth: true,
      lineStyle: { color: "#60a5fa", width: 3 },
      itemStyle: { color: "#60a5fa" },
      data: (overview.value?.trend_points ?? []).map((item: any) => item.anomalies),
    },
  ],
}));

const decisionRadarOption = computed(() => {
  const indicators = (selectedEvent.value?.ai_insight?.signal_strength ?? []).map((item: any) => ({
    name: item.name,
    max: 1,
  }));
  const values = (selectedEvent.value?.ai_insight?.signal_strength ?? []).map((item: any) => Number(item.value));
  return {
    tooltip: {},
    radar: {
      indicator: indicators,
      splitArea: { areaStyle: { color: ["rgba(255,255,255,0.03)"] } },
      axisName: { color: "#d9e8f5" },
      splitLine: { lineStyle: { color: "rgba(151,176,196,0.16)" } },
      axisLine: { lineStyle: { color: "rgba(151,176,196,0.16)" } },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: values,
            areaStyle: { color: "rgba(45,212,191,0.2)" },
            lineStyle: { color: "#2dd4bf" },
            itemStyle: { color: "#2dd4bf" },
          },
        ],
      },
    ],
  };
});

async function loadOverview() {
  const { data } = await api.get("/overview");
  overview.value = data;
}

async function loadEvents() {
  const { data } = await api.get("/events");
  events.value = data;
}

function bindCameraVideo(element: Element | null) {
  cameraVideo.value = element instanceof HTMLVideoElement ? element : null;
}

async function startCamera() {
  if (cameraStream.value) {
    if (cameraVideo.value) {
      cameraVideo.value.srcObject = cameraStream.value;
      await cameraVideo.value.play().catch(() => undefined);
    }
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia) {
    cameraError.value = "当前浏览器不支持摄像头调用。";
    return;
  }
  try {
    cameraStream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });
    await nextTick();
    if (cameraVideo.value) {
      cameraVideo.value.srcObject = cameraStream.value;
      await cameraVideo.value.play().catch(() => undefined);
    } else {
      cameraError.value = "已获取相机权限，但页面视频节点尚未准备完成，请关闭弹窗后重试。";
      return;
    }
    cameraError.value = "";
  } catch {
    cameraStream.value = null;
    cameraError.value = "相机已授权，但当前页面未成功拉起视频流，请关闭弹窗后重试。";
  }
}

function stopCamera() {
  cameraStream.value?.getTracks().forEach((track) => track.stop());
  cameraStream.value = null;
  if (cameraVideo.value) {
    cameraVideo.value.srcObject = null;
  }
}

async function handlePerceptionOpened() {
  await nextTick();
  await startCamera();
}

async function openPanel(title: string) {
  if (title === "感知接入") {
    perceptionVisible.value = true;
    return;
  }
  if (title === "视频检测") {
    videoVisible.value = true;
    return;
  }
  if (title === "决策输出") {
    decisionVisible.value = true;
    return;
  }
  fusionVisible.value = true;
}

function modalityLabel(name: string) {
  const mapping: Record<string, string> = {
    video: "视频",
    metrics: "指标",
    alerts: "告警",
    logs: "日志",
    screenshots: "截图",
  };
  return mapping[name] ?? name;
}

function modalityStatus(status: string) {
  const mapping: Record<string, string> = {
    mock_online: "模拟在线",
    online: "在线",
    offline: "离线",
  };
  return mapping[status] ?? status;
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

function adviceLevelLabel(value: string) {
  const mapping: Record<string, string> = {
    observe: "观察",
    investigate: "排查",
    escalate: "上报",
    urgent_action: "紧急处置",
  };
  return mapping[value] ?? value;
}

onMounted(async () => {
  await Promise.all([loadOverview(), loadEvents()]);
});

onBeforeUnmount(() => {
  stopCamera();
});
</script>
