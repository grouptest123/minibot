<template>
  <div class="grid">
    <section class="hero-board assistant-hero">
      <div class="hero-main">
        <h2>报告中心</h2>
        <p class="hero-subtitle">支持按日期筛选报告，按选定时间范围生成日报、周报和事件简报，并提供文档下载。</p>
      </div>
      <div class="hero-metrics compact-metrics">
        <div class="hero-metric">
          <span>报告总数</span>
          <strong>{{ reports.length }}</strong>
          <small>当前筛选结果</small>
        </div>
        <div class="hero-metric">
          <span>筛选区间</span>
          <strong>{{ rangeLabel }}</strong>
          <small>可选择单日或时间段</small>
        </div>
        <div class="hero-metric">
          <span>当前预览</span>
          <strong>{{ selected?.report_type ? reportTypeLabel(selected.report_type) : "-" }}</strong>
          <small>{{ selected?.period_label ?? "未选择" }}</small>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>筛选与生成</h3>
      </div>
      <div class="report-toolbar">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          unlink-panels
          value-format="YYYY-MM-DD"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          range-separator="至"
        />
        <el-button @click="quickToday">今天</el-button>
        <el-button @click="clearRange">清空筛选</el-button>
        <el-button type="primary" @click="generate('daily_report')">生成日报</el-button>
        <el-button @click="generate('weekly_report')">生成周报</el-button>
        <el-button @click="generate('incident_brief')">生成简报</el-button>
      </div>
      <el-table :data="reports" @row-click="selectReport" style="width: 100%">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="report_type" label="类型" width="140">
          <template #default="{ row }">
            {{ reportTypeLabel(row.report_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="period_label" label="统计区间" width="180" />
        <el-table-column prop="created_at" label="创建时间" width="200" />
        <el-table-column label="下载" width="200">
          <template #default="{ row }">
            <div class="download-actions">
              <el-button link type="primary" @click.stop="download(row, 'doc')">DOC</el-button>
              <el-button link type="primary" @click.stop="download(row, 'pdf')">PDF</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section v-if="selected" class="panel">
      <div class="section-title">
        <h3>{{ selected.title }}</h3>
      </div>
      <div class="report-meta">
        <span>类型：{{ reportTypeLabel(selected.report_type) }}</span>
        <span>区间：{{ selected.period_label }}</span>
        <span>创建时间：{{ selected.created_at }}</span>
      </div>
      <div class="report-actions">
        <el-button type="primary" @click="download(selected, 'doc')">下载 DOC</el-button>
        <el-button @click="download(selected, 'pdf')">下载 PDF</el-button>
      </div>
      <div class="report-content">{{ selected.content }}</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { api } from "../api";

const reports = ref<any[]>([]);
const selected = ref<any>();
const dateRange = ref<string[]>([]);

const rangeLabel = computed(() => {
  if (!dateRange.value?.length) return "全部";
  if (dateRange.value[0] === dateRange.value[1]) return dateRange.value[0];
  return `${dateRange.value[0]} 至 ${dateRange.value[1]}`;
});

function reportTypeLabel(type: string) {
  const mapping: Record<string, string> = {
    daily_report: "日报",
    weekly_report: "周报",
    incident_brief: "简报",
  };
  return mapping[type] ?? type;
}

function currentParams() {
  const [startDate, endDate] = dateRange.value ?? [];
  return {
    start_date: startDate || undefined,
    end_date: endDate || startDate || undefined,
  };
}

async function loadReports() {
  const { data } = await api.get("/reports", { params: currentParams() });
  reports.value = data;
  selected.value = data[0];
}

async function generate(type: string) {
  await api.post(`/reports/generate/${type}`, null, { params: currentParams() });
  ElMessage.success("报告已生成");
  await loadReports();
}

function selectReport(row: any) {
  selected.value = row;
}

async function download(row: any, format: string) {
  const response = await api.get(`/reports/export/${row.id}`, {
    params: { format },
    responseType: "blob",
  });
  const blob = new Blob([response.data], { type: response.headers["content-type"] || "application/octet-stream" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${row.title}.${format}`;
  link.click();
  window.URL.revokeObjectURL(url);
}

function quickToday() {
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  dateRange.value = [today, today];
}

function clearRange() {
  dateRange.value = [];
}

watch(dateRange, () => {
  loadReports();
});

onMounted(loadReports);
</script>
