import { defineConfig } from "vite";

const port = Number(process.env.CMDB_BACKEND_PORT || 8091);
if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error("CMDB_BACKEND_PORT must be a valid port");
}
const target = `http://127.0.0.1:${port}`;

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target,
        changeOrigin: true,
        configure(proxy) {
          proxy.on("proxyReq", (proxyReq, request) => {
            // Only our local Vite UI may use the same-origin backend bridge.
            // Keep foreign origins intact so the backend can reject them.
            const devPort = request.socket.localPort;
            const devOrigins = [`http://127.0.0.1:${devPort}`, `http://localhost:${devPort}`];
            if (devOrigins.includes(request.headers.origin)) {
              proxyReq.setHeader("Origin", target);
            }
          });
        },
      },
    },
  },
  build: { target: "es2022" },
});
