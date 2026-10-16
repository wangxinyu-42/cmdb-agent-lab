export const ERRORS = {
  provider_error: "模型服务调用失败。请检查服务端配置和模型服务状态。",
  model_not_configured: "真实模型尚未配置。请先按 README 配置后重启服务。",
  model_busy: "已有真实模型请求正在执行，请稍后重试。",
  round_budget_exceeded: "达到模型轮次上限（4 轮），本次执行停止。",
  tool_budget_exceeded: "达到工具调用上限（8 次），本次执行停止。",
  deadline_exceeded: "达到执行时间上限，本次执行停止。",
  invalid_request: "问题需为 1–2000 字，且请求格式正确。",
};
export async function jsonGet(path, signal) {
  const r = await fetch(path, { signal });
  if (!r.ok) throw new Error(`请求失败 (${r.status})`);
  return r.json();
}
export async function streamChat(question, mode, signal, onEvent) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, mode }),
    signal,
  });
  if (!response.ok) {
    const body = await response.json();
    throw new Error(ERRORS[body.error] || `请求失败 (${response.status})`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "",
    terminal = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      let boundary;
      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const data = frame
          .split("\n")
          .filter((l) => l.startsWith("data: "))
          .map((l) => l.slice(6))
          .join("\n");
        if (data) {
          const event = JSON.parse(data);
          onEvent(event);
          terminal ||= event.event === "final" || event.event === "error";
        }
      }
      if (done) break;
    }
    if (!terminal) throw new Error("连接中断，未收到完成事件。");
  } finally {
    reader.releaseLock();
  }
}
