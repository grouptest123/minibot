<template>
  <div class="grid">
    <section class="hero-board assistant-hero">
      <div class="hero-main">
        <p class="eyebrow">Conversational Trigger</p>
        <h2>通过自然语言驱动值班机器人</h2>
        <p class="hero-subtitle">从异常汇总、处置建议到日报生成，系统会显示理解任务、选择技能、调用工具和形成输出的过程。</p>
      </div>
    </section>

    <section class="panel assistant-box">
      <div class="section-title">
        <h3>对话输入</h3>
        <span class="section-caption">Prompt Console</span>
      </div>
      <el-input
        v-model="message"
        type="textarea"
        :rows="4"
        placeholder="例如：汇总今天异常情况 / 分析 14:00 告警 / 给出处置建议 / 生成今日日报"
      />
      <div style="display: flex; gap: 8px">
        <el-button type="primary" @click="submit">执行任务</el-button>
        <el-button @click="message = '给出处置建议'">建议示例</el-button>
        <el-button @click="message = '生成今日日报'">日报示例</el-button>
      </div>
    </section>

    <section v-if="result" class="panel">
      <div class="section-title">
        <h3>执行过程</h3>
        <span class="section-caption">{{ result.intent }}</span>
      </div>
      <div class="workflow-ladder">
        <div v-for="(step, index) in result.steps" :key="step" class="workflow-node">
          <span>{{ String(index + 1).padStart(2, '0') }}</span>
          <strong>{{ prettyStep(step) }}</strong>
          <p>{{ stepDetail(step) }}</p>
        </div>
      </div>
      <div class="report-content" style="margin-top: 16px">
        <strong>摘要：</strong>{{ result.summary }}

        <strong>结果：</strong>
        {{ JSON.stringify(result.payload, null, 2) }}
      </div>
    </section>
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
    understand_task: "识别用户任务目标、窗口范围和输出类型",
    select_skill: "匹配总览、建议、报告或事件分析技能",
    call_tools: "访问视频、日志、指标、案例与知识检索工具",
    compose_result: "融合证据并生成可解释输出",
  };
  return details[step] ?? step;
}

function prettyStep(step: string) {
  const mapping: Record<string, string> = {
    understand_task: "理解任务",
    select_skill: "选择技能",
    call_tools: "调用工具",
    compose_result: "形成输出",
  };
  return mapping[step] ?? step;
}
</script>

