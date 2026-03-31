<template>
  <div class="panel assistant-box">
    <div class="section-title">
      <h2>对话助手</h2>
      <el-tag type="success">ReAct Demo</el-tag>
    </div>
    <el-input
      v-model="message"
      type="textarea"
      :rows="4"
      placeholder="例如：汇总今天异常情况 / 分析 14:00 告警 / 给出处置建议 / 生成今日日报"
    />
    <div style="display: flex; gap: 8px">
      <el-button type="primary" @click="submit">执行任务</el-button>
      <el-button @click="message = '生成今日日报'">填充示例</el-button>
    </div>
    <div v-if="result" class="report-content">
      <strong>意图:</strong> {{ result.intent }}

      <strong>摘要:</strong> {{ result.summary }}

      <div class="workflow-ladder compact">
        <div v-for="(step, index) in result.steps" :key="step" class="workflow-node">
          <span>{{ String(index + 1).padStart(2, '0') }}</span>
          <strong>{{ step }}</strong>
          <p>{{ stepDetail(step) }}</p>
        </div>
      </div>

      <strong>结果:</strong>
      {{ JSON.stringify(result.payload, null, 2) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { api } from "../api";

const message = ref("汇总今天异常情况");
const result = ref<any>();

async function submit() {
  const { data } = await api.post("/chat", { message: message.value });
  result.value = data;
}

function stepDetail(step: string) {
  const details: Record<string, string> = {
    understand_task: "识别用户目标和任务类型",
    select_skill: "挑选最合适的技能与数据源",
    call_tools: "执行视频、日志、指标、知识检索等工具",
    compose_result: "汇总证据并生成建议或报告",
  };
  return details[step] ?? step;
}
</script>
