import React, { useState } from "react";
import { Icon } from "./ui.jsx";
export default function TracePanel({ events, busy }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(JSON.stringify(events, null, 2));
      setCopied(true);
    } catch {
      setCopied(false);
    }
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <aside className="panel trace-panel" aria-label="执行轨迹">
      <h2>执行轨迹</h2>
      <p className="muted trace-intro">每一步都有依据</p>
      {!events.length ? (
        <div className="trace-empty">
          <Icon name="network" size={32} />
          <p>执行后查看每一步工具调用</p>
          <span>请求 → 工具 → 结果</span>
        </div>
      ) : (
        <ol className="timeline">
          {events.map((e) => (
            <li
              key={e.sequence}
              className={e.event === "error" ? "failed" : ""}
            >
              <span className="step-dot">
                <Icon
                  name={e.event === "error" ? "close" : "check"}
                  size={13}
                />
              </span>
              <h3>
                {e.event === "start"
                  ? "接收请求"
                  : e.event === "tool"
                    ? e.name
                    : e.event === "final"
                      ? "完成回答"
                      : "执行停止"}
              </h3>
              {e.event === "start" ? (
                <p>{e.question}</p>
              ) : e.event === "tool" ? (
                <>
                  <pre className="argument">
                    {JSON.stringify(e.arguments, null, 2)}
                  </pre>
                  <p>
                    {e.result.error
                      ? "参数或工具错误：" + e.result.error
                      : e.name === "audit_assets"
                        ? `发现 ${e.result.issue_count} 项异常 (${e.result.issues.map((i) => i.asset_id).join("、") || "无"})`
                        : `返回 ${e.result.assets.length} 台设备 (${e.result.assets.map((a) => a.id).join("、") || "无匹配"})`}
                  </p>
                </>
              ) : e.event === "final" ? (
                <p>已生成查询结果与异常说明。</p>
              ) : (
                <p>{e.code}</p>
              )}
            </li>
          ))}
        </ol>
      )}
      {busy && (
        <p className="muted pulse" role="status">
          正在执行，请稍候…
        </p>
      )}
      {!!events.length && (
        <div className="raw-events">
          <details open>
            <summary>原始事件 JSON</summary>
            <pre>{JSON.stringify(events, null, 2)}</pre>
          </details>
          <button
            className="copy-button"
            onClick={copy}
            aria-label="复制原始事件"
          >
            <Icon name="copy" size={17} />
            {copied ? "已复制" : "复制"}
          </button>
          <div className="trace-id">trace_id: {events[0].trace_id}</div>
        </div>
      )}
    </aside>
  );
}
