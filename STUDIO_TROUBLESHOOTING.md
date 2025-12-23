# LangGraph Studio 故障排除指南

## 从日志中发现的问题

根据你的日志，服务器已经成功启动，但 Studio UI 无法正常工作。主要问题：

### 错误分析

1. **422 错误**（第 272 行）：
   ```
   GET /assistants/search 422 1ms
   ```
   - 这表示 Studio UI 尝试访问 `/assistants/search` 端点
   - 422 错误通常表示请求格式不正确或缺少必需参数

2. **404 错误**（第 273 行）：
   ```
   GET /favicon.ico 404 0ms
   ```
   - 这个不重要，只是浏览器请求网站图标

## 解决方案

### 方案 1：检查 API 端点

确保 API 服务器正在运行并可以访问：

```bash
# 在另一个终端窗口测试
curl http://127.0.0.1:2024/health
curl http://127.0.0.1:2024/docs
```

### 方案 2：检查浏览器控制台

1. 打开浏览器开发者工具（F12）
2. 查看 Console 标签页的错误信息
3. 查看 Network 标签页，检查哪些请求失败了

### 方案 3：使用 API 文档页面

直接访问 API 文档页面测试：
```
http://127.0.0.1:2024/docs
```

### 方案 4：检查环境变量

确保 `.env` 文件配置正确：

```bash
# 检查 .env 文件是否存在
ls -la module-1/studio/.env

# 如果不存在，从父目录复制
cp ../.env module-1/studio/.env
```

### 方案 5：使用 Python SDK 直接测试

如果 Studio UI 无法工作，可以直接使用 Python SDK：

```python
from langgraph_sdk import get_client

client = get_client(url="http://127.0.0.1:2024")

# 列出所有图形
assistants = client.assistants.list()
print(assistants)

# 运行图形
thread = {"configurable": {"thread_id": "test-123"}}
result = client.runs.create(
    assistant_id="simple_graph",
    input={"graph_state": "Hello"},
    config=thread
)
print(result)
```

### 方案 6：检查防火墙和网络

确保：
- 本地防火墙没有阻止 2024 端口
- 浏览器可以访问 `http://127.0.0.1:2024`
- 没有代理服务器干扰连接

### 方案 7：清除浏览器缓存

有时浏览器缓存会导致问题：
1. 清除浏览器缓存
2. 使用隐私模式/无痕模式打开 Studio URL
3. 尝试不同的浏览器

## 常见问题

### Q: Studio UI 显示空白页面

**A:** 检查浏览器控制台的错误信息，可能是：
- CORS 问题
- JavaScript 错误
- 网络连接问题

### Q: 422 错误

**A:** 这通常表示：
- API 端点路径不正确
- 请求参数格式不正确
- API 版本不匹配

### Q: 无法连接到本地 API

**A:** 检查：
1. `langgraph dev` 是否正在运行
2. 端口 2024 是否被占用
3. 防火墙设置

## 诊断命令

运行以下命令进行诊断：

```bash
# 1. 检查 API 是否运行
curl http://127.0.0.1:2024/health

# 2. 检查图形列表
curl http://127.0.0.1:2024/assistants

# 3. 检查 API 文档
open http://127.0.0.1:2024/docs

# 4. 检查端口是否被占用
lsof -i :2024
```

## 替代方案

如果 Studio UI 无法工作，你可以：

1. **使用 API 文档页面**：`http://127.0.0.1:2024/docs`
2. **使用 Python SDK**：直接在代码中调用 API
3. **使用 Jupyter Notebook**：在 notebook 中直接运行和测试图形

