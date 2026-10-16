import React, { useEffect, useState } from "react";
import Workbench from "./Workbench.jsx";
import AssetLedger from "./AssetLedger.jsx";
import Evaluations from "./Evaluations.jsx";
import { Icon, Modal } from "./ui.jsx";
import { jsonGet } from "./api.js";
export default function App() {
  const [page, setPage] = useState("work"),
    [mode, setMode] = useState("demo"),
    [configured, setConfigured] = useState(false),
    [about, setAbout] = useState(false);
  useEffect(() => {
    const a = new AbortController();
    jsonGet("/api/config", a.signal)
      .then((c) => setConfigured(c.llama_configured))
      .catch(() => {});
    return () => a.abort();
  }, []);
  const nav = [
    ["work", "home", "工作台"],
    ["assets", "file", "资产台账"],
    ["evals", "list", "评测结果"],
  ];
  return (
    <>
      <header className="header">
        <div className="brand">
          <span className="brand-icon">
            <Icon name="network" size={32} />
          </span>
          <div>
            <strong>CMDB Agent Lab</strong>
            <p>资产查询与稽核工作台</p>
          </div>
        </div>
        <div className="header-actions">
          <select
            aria-label="运行模式"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
          >
            <option value="demo">本地演示</option>
            <option value="llama" disabled={!configured}>
              真实模型{configured ? "" : "（未配置）"}
            </option>
          </select>
          <button className="text-button" onClick={() => setAbout(true)}>
            项目说明
          </button>
        </div>
      </header>
      <div className="shell">
        <nav className="sidebar" aria-label="主导航">
          <div>
            {nav.map(([key, icon, title]) => (
              <button
                key={key}
                className={page === key ? "nav-button active" : "nav-button"}
                aria-current={page === key ? "page" : undefined}
                onClick={() => setPage(key)}
              >
                <Icon name={icon} />
                {title}
              </button>
            ))}
          </div>
          <div className="data-note">
            <Icon name="database" size={17} />
            合成数据 · 只读查询
          </div>
        </nav>
        <main>
          {page === "work" ? (
            <Workbench key={mode} mode={mode} />
          ) : page === "assets" ? (
            <AssetLedger />
          ) : (
            <Evaluations />
          )}
        </main>
      </div>
      {about && (
        <Modal
          className="about"
          titleId="about-title"
          onClose={() => setAbout(false)}
        >
          <div className="section-heading">
            <h2 id="about-title">项目说明</h2>
            <button
              className="icon-button"
              aria-label="关闭项目说明"
              onClick={() => setAbout(false)}
            >
              <Icon name="close" />
            </button>
          </div>
          <p>
            面向 Agent 应用开发学习的 CMDB 查询与稽核演示项目，由 AI 辅助实现。
          </p>
          <p>
            本地演示使用确定性规则路由；真实模型模式需额外配置支持工具调用的模型服务。两种模式共用只读工具、参数校验与执行轨迹。
          </p>
          <p>
            数据全部为合成样例，未接入企业
            CMDB。当前评测只验证固定场景，不代表真实模型准确率、生产安全性或性能。
          </p>
          <a
            className="text-button"
            href="https://github.com/wangxinyu-42/cmdb-agent-lab"
            target="_blank"
            rel="noreferrer"
          >
            查看源码与启动说明 ↗
          </a>
        </Modal>
      )}
    </>
  );
}
