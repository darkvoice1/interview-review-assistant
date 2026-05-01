// 把时间转成更易读的中文格式。
export function formatDateTime(value) {
  if (!value) {
    return "暂无";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

// 把文档创建时间压缩成短格式，方便列表展示。
export function formatShortDate(value) {
  if (!value) {
    return "暂无";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

// 用统一规则把题目难度映射成文案。
export function formatDifficulty(value) {
  if (value >= 4) {
    return "较难";
  }
  if (value >= 2) {
    return "中等";
  }
  return "基础";
}
