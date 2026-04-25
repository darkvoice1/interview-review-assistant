<template>
  <div class="page-shell">
    <header class="hero card">
      <div>
        <p class="eyebrow">Interview Review Assistant</p>
        <h1>把零散面经笔记，整理成可持续复习的题库。</h1>
        <p class="muted intro">
          当前是项目骨架版本，已经预留文档导入、题目生成、每日复习和错题追踪页面。
        </p>
      </div>
      <nav class="nav">
        <RouterLink to="/">总览</RouterLink>
        <RouterLink to="/documents">文档导入</RouterLink>
        <RouterLink to="/review">今日复习</RouterLink>
        <RouterLink to="/wrong-questions">错题</RouterLink>
      </nav>
    </header>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from "vue-router";
</script>

<style scoped>
.hero {
  display: grid;
  gap: 20px;
  padding: 28px;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #0369a1;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  max-width: 720px;
  font-size: clamp(2rem, 4vw, 3.4rem);
  line-height: 1.05;
}

.intro {
  max-width: 680px;
  margin: 12px 0 0;
}

.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.nav a {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(14, 165, 233, 0.08);
  color: #0f172a;
  font-weight: 600;
}

.nav a.router-link-active {
  background: #0f172a;
  color: #ffffff;
}

.content {
  display: grid;
  gap: 20px;
}
</style>
