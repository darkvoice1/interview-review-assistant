<template>
  <section class="grid">
    <article class="card metric">
      <p class="label">今日待复习</p>
      <strong>18</strong>
      <span class="muted">规则题库与调度模块接入后会变成真实数据。</span>
    </article>
    <article class="card metric">
      <p class="label">已导入文档</p>
      <strong>3</strong>
      <span class="muted">后续联调后会展示文档列表接口数据。</span>
    </article>
    <article class="card metric">
      <p class="label">薄弱专题</p>
      <strong>Redis</strong>
      <span class="muted">这里会汇总最近错误率较高的知识点。</span>
    </article>
  </section>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.metric {
  padding: 24px;
}

.label {
  margin: 0 0 10px;
  color: #0369a1;
  font-size: 0.9rem;
  font-weight: 700;
}

strong {
  display: block;
  margin-bottom: 10px;
  font-size: 2rem;
}
</style>
