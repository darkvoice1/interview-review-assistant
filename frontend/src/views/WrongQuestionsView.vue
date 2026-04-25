<template>
  <section class="card panel">
    <h2 class="section-title">错题列表</h2>
    <p class="muted">这里会汇总需要重点回看的题目，并支持后续按专题筛选。</p>

    <div class="stack">
      <article class="wrong-item">
        <div>
          <strong>MySQL 索引失效的常见场景有哪些？</strong>
          <p class="muted">标签：MySQL / 索引</p>
        </div>
        <button>加入今日复习</button>
      </article>

      <article class="wrong-item">
        <div>
          <strong>线程和进程的核心区别是什么？</strong>
          <p class="muted">标签：操作系统 / 并发</p>
        </div>
        <button>加入今日复习</button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.panel {
  padding: 24px;
}

.stack {
  display: grid;
  gap: 14px;
  margin-top: 18px;
}

.wrong-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.7);
}

button {
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  background: #0369a1;
  color: white;
  cursor: pointer;
}
</style>
