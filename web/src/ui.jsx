import React, { useEffect, useRef } from "react";
export function Modal({ children, onClose, titleId, className = "" }) {
  const ref = useRef(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      className={"detail-dialog " + className}
      aria-labelledby={titleId}
    >
      {children}
    </dialog>
  );
}
function validIPv4(value) {
  const parts = value.split(".");
  return (
    parts.length === 4 &&
    parts.every((p) => /^(0|[1-9]\d{0,2})$/.test(p) && Number(p) <= 255)
  );
}
export function Icon({ name, size = 20 }) {
  const paths = {
    network: (
      <>
        <rect x="9" y="2" width="6" height="6" rx="1" />
        <rect x="2" y="16" width="6" height="6" rx="1" />
        <rect x="16" y="16" width="6" height="6" rx="1" />
        <path d="M12 8v4H5v4m7-4h7v4" />
      </>
    ),
    home: (
      <>
        <path d="m3 10 9-7 9 7v11H3Z" />
        <path d="M9 21v-7h6v7" />
      </>
    ),
    file: (
      <>
        <path d="M6 2h8l4 4v16H6Z" />
        <path d="M14 2v5h4M9 12h6m-6 4h6" />
      </>
    ),
    list: (
      <>
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M7 8h1m3 0h6M7 12h1m3 0h6M7 16h1m3 0h6" />
      </>
    ),
    database: (
      <>
        <ellipse cx="12" cy="5" rx="8" ry="3" />
        <path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0" />
      </>
    ),
    arrow: (
      <>
        <path d="M4 12h16m-6-6 6 6-6 6" />
      </>
    ),
    download: (
      <>
        <path d="M12 2v13m-5-5 5 5 5-5M4 15v6h16v-6" />
      </>
    ),
    warning: (
      <>
        <path d="m12 3 10 18H2Z" />
        <path d="M12 9v5m0 3v1" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    copy: (
      <>
        <rect x="8" y="8" width="12" height="13" rx="1" />
        <path d="M16 8V3H3v13h5" />
      </>
    ),
    search: (
      <>
        <circle cx="10" cy="10" r="7" />
        <path d="m15 15 6 6" />
      </>
    ),
    close: <path d="m5 5 14 14M5 19 19 5" />,
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.file}
    </svg>
  );
}
export function AssetTable({ assets, onSelect }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {["资产 ID", "设备名称", "环境", "负责人", "IP 地址"].map((h) => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {assets.map((a) => (
            <tr key={a.id}>
              <td>
                {onSelect ? (
                  <button className="text-button" onClick={() => onSelect(a)}>
                    {a.id}
                  </button>
                ) : (
                  a.id
                )}
              </td>
              <td>{a.name}</td>
              <td>{a.environment}</td>
              <td className={!a.owner ? "muted" : ""}>{a.owner || "待补"}</td>
              <td className={!validIPv4(a.ip) ? "muted" : ""}>
                {validIPv4(a.ip) ? a.ip : "无效地址"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function IssueList({ issues }) {
  return (
    <div className="issues">
      {issues.map((i) => (
        <div className="issue" key={i.asset_id + i.code}>
          <Icon name="warning" size={18} />
          <span>
            {i.asset_id} · {i.message}
          </span>
        </div>
      ))}
    </div>
  );
}
export function downloadJSON(value, name) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function AssetDetail({ asset, onClose }) {
  return (
    <Modal onClose={onClose} titleId="detail-title">
      <div className="section-heading">
        <h2 id="detail-title">{asset.id} 设备详情</h2>
        <button className="icon-button" aria-label="关闭详情" onClick={onClose}>
          <Icon name="close" />
        </button>
      </div>
      <dl>
        {Object.entries({
          设备名称: asset.name,
          设备类型: asset.type,
          机柜: asset.rack || "待补",
          环境: asset.environment,
          负责人: asset.owner || "待补",
          IP地址: asset.ip,
        }).map(([k, v]) => (
          <React.Fragment key={k}>
            <dt>{k}</dt>
            <dd>{v}</dd>
          </React.Fragment>
        ))}
      </dl>
      <p className="muted small">来源：synthetic_fixture · 合成演示数据</p>
    </Modal>
  );
}
