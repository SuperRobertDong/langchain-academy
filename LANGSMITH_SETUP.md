# LangSmith 配置指南

## 什么是 LangSmith？

LangSmith 是 LangChain 提供的追踪和监控工具，可以帮助你：
- 📊 **追踪**：查看模型调用的详细信息
- 🐛 **调试**：识别和修复问题
- 📈 **监控**：监控应用性能和错误率
- 🧪 **评估**：测试和比较不同的提示和模型

## 配置步骤

### 1. 获取 LangSmith API Key

1. 访问 [LangSmith 官网](https://smith.langchain.com/)
2. 登录或注册账号
3. 进入 **Settings** → **API Keys**
4. 创建新的 API Key 并复制

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
# LangSmith 配置
LANGSMITH_API_KEY=your-api-key-here
LANGSMITH_TRACING_V2=true
LANGSMITH_PROJECT=langchain-academy
```

**参数说明：**
- `LANGSMITH_API_KEY`: 你的 LangSmith API Key（必需）
- `LANGSMITH_TRACING_V2`: 启用追踪功能（设置为 `true`）
- `LANGSMITH_PROJECT`: 项目名称，用于在 LangSmith 中组织追踪数据

### 3. 查看追踪数据

配置完成后，运行你的代码，然后：

1. 访问 [LangSmith Dashboard](https://smith.langchain.com/)
2. 在左侧导航栏点击 **Tracing**
3. 选择你的项目（如 "langchain-academy"）
4. 查看模型调用的详细信息

## 常见问题

### Q: 遇到 403 Forbidden 错误怎么办？

**A:** 可能的原因：
1. API Key 无效或已过期
2. API Key 权限不足
3. 网络连接问题

**解决方案：**
- 检查 API Key 是否正确
- 在 LangSmith 设置中重新生成 API Key
- 如果不需要追踪，可以禁用 LangSmith（见下方）

### Q: 如何禁用 LangSmith 追踪？

**A:** 在代码中添加：

```python
import os
os.environ.pop("LANGSMITH_TRACING_V2", None)
os.environ.pop("LANGSMITH_TRACING", None)
```

或者在 `.env` 文件中设置：

```bash
LANGSMITH_TRACING_V2=false
LANGSMITH_TRACING=false
```

### Q: 如何更改项目名称？

**A:** 在 `.env` 文件中修改 `LANGSMITH_PROJECT` 的值：

```bash
LANGSMITH_PROJECT=my-custom-project-name
```

## LangSmith 界面说明

从你的截图可以看到：

1. **左侧导航栏**：
   - **Tracing**: 查看追踪数据（显示有 1 条记录）
   - **Monitoring**: 监控仪表板
   - **Evaluation**: 评估和测试
   - **Studio**: 可视化图形编辑器

2. **主界面**：
   - **"default" 项目**：显示追踪统计
   - **Run Count**: 运行次数
   - **Error Rate**: 错误率
   - **Latency**: 延迟时间

3. **项目设置**：
   - 点击项目名称可以查看详细信息
   - 可以创建新项目来组织不同的实验

## 最佳实践

1. **为不同模块创建不同项目**：
   ```bash
   # module-1
   LANGSMITH_PROJECT=module-1-agent
   
   # module-2
   LANGSMITH_PROJECT=module-2-chatbot
   ```

2. **使用有意义的项目名称**：
   - 使用描述性的名称，如 `langchain-academy-module-1`
   - 避免使用默认的 "default"

3. **定期查看追踪数据**：
   - 检查错误率
   - 监控延迟时间
   - 优化提示和模型参数

## 相关链接

- [LangSmith 官方文档](https://docs.langchain.com/langsmith)
- [LangSmith 快速开始](https://docs.langchain.com/langsmith/quick-start)
- [LangSmith API 文档](https://docs.langchain.com/langsmith/api-reference)

