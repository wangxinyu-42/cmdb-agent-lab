import React, { useEffect, useState } from "react";
import { AssetTable, AssetDetail } from "./ui.jsx";
import { jsonGet } from "./api.js";
export default function AssetLedger() {
  const [assets, setAssets] = useState([]),
    [rack, setRack] = useState(""),
    [env, setEnv] = useState(""),
    [search, setSearch] = useState(""),
    [error, setError] = useState(""),
    [selected, setSelected] = useState(null);
  useEffect(() => {
    const a = new AbortController();
    jsonGet("/api/assets", a.signal)
      .then((r) => setAssets(r.assets))
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => a.abort();
  }, []);
  const filtered = assets.filter(
    (a) =>
      (!rack || a.rack === rack) &&
      (!env || a.environment === env) &&
      (!search ||
        `${a.id} ${a.name} ${a.owner}`
          .toLowerCase()
          .includes(search.toLowerCase())),
  );
  return (
    <section className="panel full-panel">
      <h1>资产台账</h1>
      <p className="muted subtitle">
        8 条合成资产，包含 3 项预设数据异常，用于验证查询与稽核。
      </p>
      <div className="filters">
        <label>
          搜索设备
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="ID、名称或负责人"
          />
        </label>
        <label>
          机柜
          <select value={rack} onChange={(e) => setRack(e.target.value)}>
            <option value="">所有机柜</option>
            {["A01", "B02", "C03"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label>
          环境
          <select value={env} onChange={(e) => setEnv(e.target.value)}>
            <option value="">所有环境</option>
            <option>test</option>
            <option>dev</option>
          </select>
        </label>
        <button
          className="secondary"
          onClick={() => {
            setSearch("");
            setRack("");
            setEnv("");
          }}
        >
          重置
        </button>
      </div>
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : (
        <>
          <p className="muted small">
            匹配 {filtered.length} 条记录 · 点击资产 ID 查看原始字段
          </p>
          {filtered.length ? (
            <AssetTable assets={filtered} onSelect={setSelected} />
          ) : (
            <p className="empty-line">没有匹配设备，请调整过滤条件。</p>
          )}
        </>
      )}
      {selected && (
        <AssetDetail asset={selected} onClose={() => setSelected(null)} />
      )}
    </section>
  );
}
