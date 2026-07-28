# JobPulse 本地启动与关闭

本文档是 JobPulse 本地运行方式的唯一基准。默认端口：

- 前端：`http://127.0.0.1:3100`
- 后端：`http://127.0.0.1:8100`

线上站点与 Railway 后端独立运行，启动或关闭本地服务不会影响线上环境。

## 一、首次准备

要求：

- Python 3.10+
- Node.js 22.13+

在项目根目录安装后端依赖并初始化演示数据库：

```powershell
python -m pip install -e ".[dev]"
python -m src.db.init_db
```

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
