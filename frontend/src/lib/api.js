const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

/**
 * 统一处理前端到后端的请求。
 * 这样每个页面只关心“要什么数据”，不用重复写错误处理。
 */
async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    let message = "请求失败，请稍后重试。";

    try {
      const errorData = await response.json();
      message = errorData.detail ?? errorData.message ?? message;
    } catch {
      message = response.statusText || message;
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

// 获取 JSON 数据。
export function apiGet(path) {
  return request(path);
}

// 提交 JSON 数据。
export function apiPost(path, body) {
  const options = { method: "POST" };

  if (body !== undefined) {
    options.headers = {
      "Content-Type": "application/json",
    };
    options.body = JSON.stringify(body);
  }

  return request(path, options);
}

// 上传文件时使用 FormData，避免手动设置 boundary。
export function apiUpload(path, file, fieldName = "file") {
  const formData = new FormData();
  formData.append(fieldName, file);

  return request(path, {
    method: "POST",
    body: formData,
  });
}
