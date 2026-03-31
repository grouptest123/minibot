<template>
  <div class="grid">
    <section class="hero-board assistant-hero">
      <div class="hero-main">
        <p class="eyebrow">Auto Reporting</p>
        <h2>自动输出日报、周报与事件简报</h2>
        <p class="hero-subtitle">报告中心用于展示信息生成能力，体现值班闭环最后一环的自动沉淀与归档。</p>
      </div>
      <div class="banner-badges">
        <span>日报</span>
        <span>周报</span>
        <span>事件简报</span>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <h3>报告中心</h3>
        <span class="section-caption">Generated Reports</span>
      </div>
      <div style="display: flex; gap: 8px; margin-bottom: 14px">
        <el-button type="primary" @click="generate('daily_report')">生成日报</el-button>
        <el-button @click="generate('weekly_report')">生成周报</el-button>
        <el-button @click="generate('incident_brief')">生成简报</el-button>
      </div>
      <el-table :data="reports" @row-click="selectReport" style="width: 100%">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="report_type" label="类型" width="160" />
        <el-table-column prop="created_at" label="创建时间" width="220" />
      </el-table>
    </section>

    <section v-if="selected" class="panel">
      <div class="section-title">
        <h3>{{ selected.title }}</h3>
        <span class="section-caption">{{ selected.format }}</span>
      </div>
      <div class="report-content">{{ selected.content }}</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { api } from "../api";

const reports = ref<any[]>([]);
const selected = ref<any>();

async function loadReports() {
  const { data } = await api.get("/reports");
  reports.value = data;
  selected.value = data[0];
}

async function generate(type: string) {
  await api.post(`/reports/generate/${type}`);
  ElMessage.success("报告已生成");
  await loadReports();
}

function selectReport(row: any) {
  selected.value = row;
}

onMounted(loadReports);
</script>

