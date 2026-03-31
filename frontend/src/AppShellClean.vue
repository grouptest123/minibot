<template>
  <div class="app-shell pro-shell">
    <aside class="sidebar pro-sidebar">
      <div class="sidebar-top">
        <h1>智能值班闭环</h1>
      </div>

      <div class="sidebar-status">
        <div class="status-chip">
          <span class="status-dot"></span>
          在线
        </div>
      </div>

      <nav class="nav-list">
        <RouterLink to="/">总览</RouterLink>
        <RouterLink to="/events">事件</RouterLink>
        <RouterLink to="/reports">报告</RouterLink>
        <RouterLink to="/assistant">助手</RouterLink>
      </nav>
    </aside>

    <main class="content pro-content">
      <div class="top-banner">
        <h2>值班态势</h2>
      </div>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts"></script>

