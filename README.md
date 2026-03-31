# 智能值班闭环 Demo 系统

面向银行或工业生产环境的值班辅助演示系统，围绕以下闭环运行：

信息融合 -> 异常识别 -> 处置建议 -> 信息生成

## 快速启动

本地启动：

```powershell
./scripts/start_backend.ps1
./scripts/start_frontend.ps1
```

- 后端: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`
- 前端: `http://127.0.0.1:5173`

Docker 启动：

```powershell
docker compose up --build
```

