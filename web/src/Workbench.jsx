import React, { useRef, useState, useEffect } from "react";
import TracePanel from "./TracePanel.jsx";
import {
  AssetTable,
  IssueList,
  AssetDetail,
  Icon,
  downloadJSON,
} from "./ui.jsx";
import { streamChat, ERRORS } from "./api.js";
export default function Workbench({ mode }) {
  const [question, setQuestion] = useState(
    "查询 A01 机柜的设备，并检查数据异常",
  );
  const [events, setEvents] = useState([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [asset, setAsset] = useState(null);
  const controller = useRef(null);
  useEffect(() => () => controller.current?.abort(), []);
  const final = events.find((e) => e.event === "final");
  async function execute(e) {
    e.preventDefault();
    if (busy || !question.trim()) return;
    const abort = new AbortController();
    controller.current = abort;
    setBusy(true);
    setError("");
    setEvents([]);
    try {
      await streamChat(question, mode, abort.signal, (event) => {
        setEvents((old) => [...old, event]);
        if (event.event === "error")
          setError(ERRORS[event.code] || `执行失败：${event.code}`);
      });
    } catch (e) {
      setError(
        e.name === "AbortError"
          ? "本次执行已取消。模型请求可能仍在服务端等待超时。"
          : e.message,
      );
    } finally {
      setBusy(false);
      controller.current = null;
    }
  }
  const samples = [
    "查询 A01 机柜的设备",
    "稽核所有资产异常",
    "查看 SYN-003 详情",
  ];
  return (
    <div className="work-grid">
      <div className="work-main">
        <section className="panel composer">
          <h1>运维问题，从这里开始</h1>
          <p className="muted subtitle">
            用自然语言查询资产，检查数据质量，并查看执行依据。
          </p>
          <div className="samples">
            {samples.map((s) => (
              <button disabled={busy} key={s} onClick={() => setQuestion(s)}>
                <Icon name="file" size={17} />
                {s}
              </button>
            ))}
          </div>
          <form onSubmit={execute}>
            <label htmlFor="question">输入你的问题</label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              maxLength={2000}
              required
              disabled={busy}
            />
            <div className="form-actions">
              {busy ? (
                <button
                  type="button"
                  className="secondary"
                  onClick={() => controller.current?.abort()}
                >
                  取消执行
                </button>
              ) : null}
              <button
                type="submit"
                className="primary"
                disabled={busy || !question.trim()}
              >
                <Icon name="arrow" />
                {busy ? "正在执行" : "执行查询"}
              </button>
            </div>
          </form>
        </section>
        <section className="panel results" aria-live="polite">
          <div className="section-heading">
            <h2>查询结果</h2>
            <button
              className="text-button"
              disabled={!events.length || busy}
              onClick={() =>
                downloadJSON(
                  { mode, events },
                  `cmdb-trace-${events[0].trace_id}.json`,
                )
              }
            >
              <Icon name="download" size={17} />
              下载记录
            </button>
          </div>
          {error && (
            <div className="error" role="alert">
              {error}
            </div>
          )}
          {final ? (
            <>
              <p className="answer">{final.answer}</p>
              {mode === "llama" && (
                <p className="muted small">
                  自然语言说明由模型生成，请核对下方工具依据。
                </p>
              )}
              {final.assets.length > 0 ? (
                <AssetTable assets={final.assets} onSelect={setAsset} />
              ) : (
                <p className="muted small">没有可展示的设备记录。</p>
              )}
              {final.issues.length > 0 && (
                <>
                  <h3 className="issues-heading">数据异常</h3>
                  <IssueList issues={final.issues} />
                </>
              )}
            </>
          ) : (
            !error && (
              <div className="result-empty">
                <Icon name="search" size={30} />
                <p>
                  {busy
                    ? "正在读取资产与稽核依据…"
                    : "输入问题，开始一次有依据的查询"}
                </p>
                <span>选择示例后，点击「执行查询」</span>
              </div>
            )
          )}
        </section>
      </div>
      <TracePanel events={events} busy={busy} />
      {asset && <AssetDetail asset={asset} onClose={() => setAsset(null)} />}
    </div>
  );
}
