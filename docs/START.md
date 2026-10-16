# 启动与排错

## Windows

1. 安装 Python 3.11 或更新版本，安装时启用 PATH。使用 `python --version` 或 `py -3 --version` 检查。
2. 下载完整仓库并解压，目录中应有 `run.py`、`cmdb_agent` 和 `web/dist`。
3. 双击 `start.cmd`，或在当前目录打开 PowerShell：

```powershell
python run.py
```

4. 浏览器访问 http://127.0.0.1:8091。终端保留运行；按 Ctrl+C 停止。

## macOS / Linux

```bash
python3 --version
python3 run.py
# 或 sh start.sh
```

## 排错

| 症状 | 处理 |
| --- | --- |
| python 无法识别 / 跳转应用商店 | 使用 `py -3` 或安装 Python 并启用 PATH；确认至少 3.11 |
| Port 8091 unavailable | `python run.py --port 8092`，访问终端显示的新地址；不必关闭其他服务 |
| Missing prebuilt web/dist | 下载完整仓库；开发者可进入 web 执行 npm ci、npm run build |
| 浏览器未自动打开 | 手动复制终端中的 http://127.0.0.1:端口 |
| 真实模型选项不可用 | 同一终端设置 LLAMA_BASE_URL 与 LLAMA_MODEL 后重启 Python；查看 README 的地址限制 |
| provider_error | 检查模型服务、模型 ID、chat template 与工具调用支持；原始服务错误不会传到前端 |
| model_busy | 当前只允许一个真实模型请求；等待已发请求结束再执行 |
| 修改前端后页面不更新 | 进入 web 执行 npm run build，浏览器刷新 |
| Vite 开发模式执行失败 | Python 后端需使用默认 8091；正式演示应直接访问 Python 服务 |

## API 示例

启动后，在另一个终端运行（不依赖 curl）：

```bash
python -c "import urllib.request,json; r=urllib.request.Request('http://127.0.0.1:8091/api/chat',data=json.dumps({'question':'查询 A01 机柜的设备，并检查数据异常'}).encode(),headers={'Content-Type':'application/json'}); print(urllib.request.urlopen(r).read().decode())"
```

只读接口：`GET /api/health`、`GET /api/config`、`GET /api/assets?rack=A01`、`GET /api/evals`。`POST /api/chat` 接受 JSON `{question, mode}`，mode 为 `demo` 或已配置的 `llama`；返回 SSE。

刷新页面会丢失当前查询轨迹。需要留存时先点击“下载记录”。下载文件只包含本次模式和事件，不包含模型凭据。
