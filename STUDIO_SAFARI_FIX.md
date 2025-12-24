# Safari 浏览器访问 LangGraph Studio 解决方案

## 问题

Safari 浏览器默认会阻止通过 HTTP 协议访问 localhost，导致无法连接到 LangGraph Studio。

## 解决方案

### 方案 1：使用 --tunnel 标志（推荐）

使用 `--tunnel` 标志启动服务器，这会创建一个公共隧道（通过 Cloudflare），绕过浏览器的 localhost 限制：

```bash
cd module-1/studio
langgraph dev --tunnel
```

启动后，你会看到类似这样的输出：
```
- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=https://your-tunnel-url.cloudflare.com
- 📚 API Docs: http://127.0.0.1:2024/docs
```

**优点：**
- 可以在任何浏览器中使用，包括 Safari
- 可以从其他设备访问（如果需要）
- 不需要修改浏览器设置

**缺点：**
- 需要网络连接（创建隧道）
- 隧道 URL 是公开的（但通常很难被猜到）

### 方案 2：使用其他浏览器

使用 Chrome、Firefox 或 Edge 浏览器：

1. 复制 Studio UI URL：
   ```
   https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
   ```

2. 在 Chrome/Firefox/Edge 中打开这个 URL

**优点：**
- 简单直接
- 不需要额外配置

**缺点：**
- 需要安装其他浏览器
- Safari 仍然无法使用

### 方案 3：修改 Safari 设置（不推荐）

可以尝试修改 Safari 的设置，但通常不推荐，因为这是 Safari 的安全特性。

## 推荐做法

**开发环境：**
- 使用 `--tunnel` 标志，这样可以在任何浏览器中工作

**生产环境：**
- 使用 LangSmith Deployment，不需要本地开发服务器

## 快速命令

```bash
# 在 module-1/studio 目录下
langgraph dev --tunnel
```

