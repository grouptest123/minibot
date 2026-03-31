<template>
  <div class="app-shell pro-shell">
    <aside class="sidebar pro-sidebar">
      <div class="sidebar-top">
        <p class="eyebrow">Closed-Loop Duty</p>
        <h1>智能值班闭环</h1>
        <p class="sidebar-subtitle">面向值班中控、异常研判与报告生成的演示控制台</p>
      </div>

      <div class="sidebar-status">
        <div class="status-chip">
          <span class="status-dot"></span>
          演示环境在线
        </div>
        <div class="status-grid">
          <div>
            <small>运行模式</small>
            <strong>Single-Node Demo</strong>
          </div>
          <div>
            <small>数据策略</small>
            <strong>Fusion + AI Insight</strong>
          </div>
        </div>
      </div>

      <nav class="nav-list">
        <RouterLink to="/">态势总览</RouterLink>
        <RouterLink to="/events">事件工作台</RouterLink>
        <RouterLink to="/reports">报告中心</RouterLink>
        <RouterLink to="/assistant">机器人助手</RouterLink>
      </nav>
    </aside>

    <main class="content pro-content">
      <div class="top-banner">
        <div>
          <p class="eyebrow">Mission Board</p>
          <h2>值班态势可视化与智能处置流程</h2>
        </div>
        <div class="banner-badges">
          <span>多模态融合</span>
          <span>视频异常追溯</span>
          <span>建议生成</span>
        </div>
      </div>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts"></script>

