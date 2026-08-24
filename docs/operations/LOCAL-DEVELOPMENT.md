# JobPulse 本地启动与关闭

本文档是 JobPulse 本地运行方式的唯一基准。默认端口：

- 前端：`http://127.0.0.1:3100`
- 后端：`http://127.0.0.1:8100`

线上站点与 Railway 后端独立运行，启动或关闭本地服务不会影响线上环境。

## 零、推荐：一键启动

在 Windows 资源管理器中双击项目根目录的 `start.cmd`，或者在 PowerShell 中运行：

```powershell
.\start.ps1
```

脚本会自动检查 Python 与 Node.js、按需安装缺失依赖；仅当后端尚未运行时，才会先校验并升级数据库，再在两个独立终端中启动前后端。前端进程会自动使用本地 API，服务就绪后浏览器将打开产品 Demo。

如果不希望自动打开浏览器：

```powershell
.\start.ps1 -NoBrowser
```

再次执行脚本时，如果服务已经运行，不会重复启动，也不会触碰正在使用的 SQLite 数据库。关闭服务时，在两个服务终端中分别按 `Ctrl+C`。

## 一、首次准备

要求：

- Python 3.10+
- Node.js 22.13+

在项目根目录安装后端依赖并初始化演示数据库：

```powershell
python -m pip install -e ".[dev]"
python -m src.db.init_db
```

`init_db` 不再使用 `create_all()` 伪装正式迁移：

- 空库直接执行 Alembic 到最新版本；
- 已有版本库只执行尚未应用的 revision；
- 未版本化旧库必须与 M0 的 7 表、字段、索引、检查约束和外键完全一致；
- 校验通过后先在数据库旁生成 `*.pre-migration-*.bak`，再 stamp 基线并升级；
- 备份名包含微秒时间，若显式指定的备份文件已经存在则拒绝覆盖；
- 同一 SQLite 文件的并发迁移由跨进程独占锁串行化，等待超时会停止而不是强行执行；
- 校验或升级失败会停止启动；升级失败时自动用备份恢复；
- Demo 重置只重置数据，不创建或修改 schema。

迁移 SQLite 前必须停止所有正在读写该文件的后端进程；不要在服务运行中单独执行 `init_db`，也不要直接对未知旧库运行 `alembic stamp`。真实 `data/jobpulse.db` 第一次按新流程启动时会产生备份；确认产品正常后也建议保留该备份一段时间。

当前 Docker/Railway 方式按单实例运行设计。多实例部署时不得让每个副本同时迁移同一数据库，必须改为一个独立迁移任务完成后再启动应用副本；这一项与真实 PostgreSQL 迁移测试同属 R1 上线门禁。

安装前端依赖：

```powershell
Set-Location web
npm install
Set-Location ..
```

确认 `web/.env.local` 指向本地后端：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8100/api/v1
```

## 二、启动后端

在项目根目录打开一个 PowerShell 终端：

```powershell
python -m uvicorn src.main:app --host 127.0.0.1 --port 8100 --reload
```

启动成功后可访问：

- 健康检查：<http://127.0.0.1:8100/health>
- API 文档：<http://127.0.0.1:8100/docs>

健康检查应返回：

```json
{"status":"ok"}
```

## 三、启动前端

保持后端终端运行，另开一个 PowerShell 终端：

```powershell
Set-Location web
npm run dev -- --webpack --hostname 127.0.0.1 --port 3100
```

显式使用 Webpack，是为了规避 Windows 中文项目路径下 Turbopack 的兼容性问题。

启动成功后可访问：

- SaaS 官网：<http://127.0.0.1:3100>
- 产品后台：<http://127.0.0.1:3100/dashboard>
- 作品集案例：<http://127.0.0.1:3100/case-study>

## 四、正常关闭

分别切换到前端和后端运行所在的终端，按：

```text
Ctrl+C
```

终端询问是否终止批处理作业时，输入 `Y` 并回车。前端与后端需要分别关闭。

## 五、终端已关闭但端口仍被占用

仅在无法回到原运行终端时使用以下 PowerShell 命令。

关闭后端 `8100` 端口对应进程：

```powershell
$processId = Get-NetTCPConnection -LocalPort 8100 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique
if ($processId) { Stop-Process -Id $processId }
```

关闭前端 `3100` 端口对应进程：

```powershell
$processId = Get-NetTCPConnection -LocalPort 3100 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique
if ($processId) { Stop-Process -Id $processId }
```

再次运行下面的命令，如果没有输出，说明端口已经释放：

```powershell
Get-NetTCPConnection -LocalPort 8100,3100 -State Listen -ErrorAction SilentlyContinue
```

## 六、常见问题

### 前端提示无法连接后端

依次检查：

1. `http://127.0.0.1:8100/health` 是否返回 `{"status":"ok"}`。
2. `web/.env.local` 是否指向 `http://127.0.0.1:8100/api/v1`。
3. 修改 `.env.local` 后是否重新启动了前端。

### 端口已被占用

先确认是否已有一套 JobPulse 服务正在运行。需要重启时，按照“终端已关闭但端口仍被占用”一节释放对应端口，再重新启动。

### 只想查看线上版本

不需要启动任何本地服务，直接访问：

- 线上官网：<https://jobpulse-product-demo.tongqtang.chatgpt.site>
- 线上后台：<https://jobpulse-product-demo.tongqtang.chatgpt.site/dashboard>
- 线上后端健康检查：<https://jobpulse-api-production.up.railway.app/health>
