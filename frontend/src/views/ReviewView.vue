<template>
  <section class="card panel">
    <div class="header">
      <div>
        <h2 class="section-title">今日复习</h2>
        <p class="muted">先展示一题一页的复习卡片，后面再接入真实题单接口。</p>
      </div>
      <span class="badge">待完成 18 题</span>
    </div>

    <article class="question-card">
      <p class="muted">来源：Redis Interview Notes</p>
      <h3>什么是 Redis 的 AOF 持久化？</h3>
      <p class="answer">答案区、展开逻辑和反馈提交会在下一阶段接入。</p>
    </article>

    <div class="actions">
      <button class="ghost">不会</button>
      <button class="ghost">模糊</button>
      <button class="solid">会</button>
    </div>
  </section>
</template>

<style scoped>
.panel {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.badge {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(14, 165, 233, 0.12);
  color: #0369a1;
  font-weight: 700;
}

.question-card {
  margin: 20px 0;
  padding: 24px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(226, 232, 240, 0.7));
}

.question-card h3 {
  margin: 8px 0 12px;
  font-size: 1.55rem;
}

.answer {
  color: #334155;
}

.actions {
  display: flex;
  gap: 12px;
}

button {
  border: none;
  border-radius: 14px;
  padding: 12px 18px;
  cursor: pointer;
}

.ghost {
  background: rgba(15, 23, 42, 0.08);
  color: #0f172a;
}

.solid {
  background: #0f172a;
  color: white;
}
</style>
