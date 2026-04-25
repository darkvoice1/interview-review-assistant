<template>
  <section class="card panel">
    <h2 class="section-title">文档导入</h2>
    <p class="muted">
      这个页面用于上传 Markdown 面经，并展示解析结果、知识点数量和生成题目数量。
    </p>

    <div class="dropzone">
      <span>将 Markdown 文件拖到这里，或点击后接入上传组件</span>
    </div>

    <div class="list">
      <div class="item">
        <strong>redis.md</strong>
        <span class="muted">12 个知识点 / 36 道题</span>
      </div>
      <div class="item">
        <strong>mysql.md</strong>
        <span class="muted">9 个知识点 / 25 道题</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  padding: 24px;
}

.dropzone {
  display: grid;
  place-items: center;
  min-height: 170px;
  margin: 20px 0;
  border: 2px dashed rgba(3, 105, 161, 0.35);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.5);
  text-align: center;
}

.list {
  display: grid;
  gap: 12px;
}

.item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.9);
}
</style>
