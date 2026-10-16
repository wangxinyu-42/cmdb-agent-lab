import React, { useEffect, useState } from "react";
import { Icon, downloadJSON } from "./ui.jsx";
import { jsonGet } from "./api.js";
export default function Evaluations() {
  const [report, setReport] = useState(null),
    [error, setError] = useState("");
  useEffect(() => {
    const a = new AbortController();
    jsonGet("/api/evals", a.signal)
      .then((r) => {
        if (r.error)
          throw new Error(
            "尚无评测报告，请运行 python -m cmdb_agent.evaluation",
          );
        setReport(r);
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => a.abort();
  }, []);
  return (
    <section className="panel full-panel">
      <div className="section-heading">
        <h1>评测结果</h1>
        {report && (
          <button
            className="text-button"
            onClick={() => downloadJSON(report, "cmdb-evaluation.json")}
          >
            <Icon name="download" size={17} />
            下载报告
          </button>
        )}
      </div>
      <p className="muted subtitle">
        固定测试集的实际运行记录，可重复执行和检查每条断言。
      </p>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {report && (
        <>
          <div className="evaluation-summary">
            <strong>
              {report.passed} / {report.total}
            </strong>
            <span>
              通过 ·{" "}
              {report.provider === "demo" ? "本地确定性演示" : "真实模型"}
            </span>
          </div>
          <p className="muted small">{report.scope}</p>
          <p className="muted small">
            报告时间：{new Date(report.generated_at).toLocaleString("zh-CN")} ·
            Python {report.python}
          </p>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>用例</th>
                  <th>输入问题</th>
                  <th>工具链</th>
                  <th>结果</th>
                </tr>
              </thead>
              <tbody>
                {report.cases.map((c) => (
                  <tr key={c.id}>
                    <td>{c.id}</td>
                    <td>{c.question}</td>
                    <td>
                      <code>{c.actual_tools.join(" → ") || "无需调用"}</code>
                    </td>
                    <td className={c.passed ? "passed" : "failed-text"}>
                      {c.passed ? "通过" : "失败"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <details className="report-details">
            <summary>数据指纹与断言详情</summary>
            <pre>{JSON.stringify(report, null, 2)}</pre>
          </details>
        </>
      )}
    </section>
  );
}
