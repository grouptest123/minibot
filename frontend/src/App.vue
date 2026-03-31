<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Duty Closed Loop</p>
        <h1>智能值班闭环 Demo</h1>
      </div>
      <nav class="nav-list">
        <RouterLink to="/">总览</RouterLink>
        <RouterLink to="/events">事件详情</RouterLink>
        <RouterLink to="/reports">报告中心</RouterLink>
        <RouterLink to="/assistant">对话助手</RouterLink>
      </nav>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts"></script>

