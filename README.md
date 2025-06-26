# AI对话诗人 - 大语言模型参数调优展示工具

## 1. 需求分析

### 1.1 项目背景

在人工智能基础课程中，学生需要理解大语言模型参数对生成结果的影响。本项目通过诗歌创作直观展示不同参数组合（`temperature` 和 `top_p`）对文本生成的影响。

#### 1.2 核心需求

| 需求类别   | 具体功能描述 |
|------------|--------------|
| **参数对比** | 直观展示不同 `temperature` 和 `top_p` 参数组合对诗歌创作的影响 |
| **用户交互** | 友好的命令行交互体验 |
| **输入验证** | 验证用户输入符合规范 |
| **输出规范** | 生成符合 Schema 的 JSON 输出 |
| **安全防护** | 敏感词过滤和指令注入防护 |
| **响应机制** | 实现 API 调用的流式输出效果 |
| **异常处理** | 健壮的 API 错误处理和重试机制 |

#### 1.3 非功能性需求

- **教学性**：清晰展示参数调优原理  
- **可靠性**：API错误处理和本地回退机制  
- **可维护性**：模块化设计，代码可读性强  
- **安全性**：输入预处理和内容过滤  

---

## 2. 技术选型

### 2.1 核心框架

| 技术组件       | 版本    | 选择理由                     |
|----------------|---------|------------------------------|
| `Python`       | 3.9+    | 丰富的AI生态，简洁语法       |
| `DeepSeek API` | v1      | 优秀的中文处理能力，免费API  |
| `requests`     | 2.31+   | 高效的HTTP请求处理           |

### 2.2 数据处理

| 组件          | 功能                    |
|---------------|-------------------------|
| `jsonschema`  | 输入输出验证            |
| `re`          | 正则表达式处理          |
| `json`        | JSON序列化/反序列化     |

### 2.3 辅助功能

| 组件        | 用途            |
|-------------|-----------------|
| `datetime`  | 时间处理        |
| `time`      | 延时和计时      |
| `sys`       | 系统交互        |

## 3. 实现细节

### 3.1 系统架构
<img width="567" alt="67d9d0dde33b80f46e1c3a2e3f699df5" src="https://github.com/user-attachments/assets/20616c88-038c-4bfb-a360-4a1e8a8dd1b3" />

### 3.2 关键算法实现

#### 3.2.1 参数组合策略
```python
param_combinations = [
    {"temperature": 0.3, "top_p": 0.5, "label": "保守创作"},
    {"temperature": 0.3, "top_p": 0.9, "label": "聚焦核心"},
    {"temperature": 1.2, "top_p": 0.5, "label": "创意发散"},
    {"temperature": 1.2, "top_p": 0.95, "label": "自由创作"}
]
```

### 3.2.2 流式响应处理
```python
for line in response.iter_lines():
    if line:
        decoded_line = line.decode('utf-8')
        if decoded_line.startswith('data: '):
            json_data = decoded_line[6:]
            if json_data != '[DONE]':
                try:
                    data = json.loads(json_data)
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            print(content, end='', flush=True)
                            full_content += content
                    time.sleep(0.02)  # 添加延时实现自然输出效果
                except JSONDecodeError:
                    pass  # 忽略JSON解析错误
```

### 3.2.3 安全防护机制
```python
def filter_sensitive_words(text):
    """过滤文本中的敏感词"""
    for word in SENSITIVE_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        text = pattern.sub('***', text)
    return text

def prevent_prompt_injection(prompt):
    """防止指令注入攻击"""
    # 移除可能用于注入的特殊字符
    prompt = re.sub(r'[;\\/*]', '', prompt)
    # 限制输入长度
```

### 3.3 模块设计
| 模块       | 功能                     | 关键函数                          |
|------------|--------------------------|-----------------------------------|
| 输入处理   | 获取并验证用户输入       | `get_user_input()`, `validate_input()` |
| API交互    | 调用DeepSeek API         | `generate_poem()`, `animate_loading()` |
| 参数管理   | 参数组合与影响分析       | `display_parameter_comparison()`, `get_style_description()` |
| 输出处理   | 结果保存与展示           | `save_results_to_json()`, `display_parameter_impact()` |
| 安全模块   | 内容过滤与防护           | `filter_sensitive_words()`, `prevent_prompt_injection()` |
| 应急处理   | API失败回退              | `generate_example_poem()`         |

---

## 4. 评估对比

### 4.1 参数影响分析
| 参数组合   | 温度 | top_p | 创作特点         | 典型输出特征             |
|------------|------|-------|------------------|--------------------------|
| 保守创作   | 0.3  | 0.5   | 严谨工整，主题集中 | 传统格律，用词规范       |
| 聚焦核心   | 0.3  | 0.9   | 主题明确，语言规范 | 主题突出，词汇多样       |
| 创意发散   | 1.2  | 0.5   | 创意丰富，表达新颖 | 意象独特，结构创新       |
| 自由创作   | 1.2  | 0.95  | 自由奔放，富有想象力 | 自由体，情感强烈         |

## 4.2 性能评估

**测试主题：** "春天"（8行现代诗）

| 指标               | 结果                        |
|--------------------|-----------------------------|
| 平均API响应时间    | 12.3秒/诗歌                 |
| 成功率             | 92% (37/40次调用)           |
| 重试成功率         | 85% (失败后重试成功比例)    |
| 完整流程时间       | 约65秒(4首诗歌)             |

## 5. 反思与改进

### 5.1 项目优势  
1. **直观的参数展示**：四组精心设计的参数组合清晰展示 `temperature` 和 `top_p` 的相互作用  
2. **健壮的错误处理**：API重试机制+本地回退确保演示连续性  
3. **流式输出体验**：实时生成效果增强教学演示的吸引力  
4. **全面的安全措施**：敏感词过滤和指令注入防护双重保障  
5. **模块化设计**：六大功能模块职责分明，便于维护扩展  

### 5.2 局限性
1. 诗歌质量评估依赖规则而非AI分析  
2. 参数组合固定，缺乏用户自定义选项  
3. 本地回退的示例诗歌多样性不足  

## 5.3 改进方向

1. **集成诗歌质量评估模型**：开发韵律、意境评分系统  
2. **支持多模型对比**：实现 DeepSeek vs GPT vs 文心一言的横向对比  
3. **实现历史记录查看功能**：保存并展示历次生成结果  
4. **开发Web界面**：提供图形化操作界面，增强用户体验  
5. **创建学习路径指导**：结构化参数调优学习路线图  
6. **扩展创作类型**：支持故事生成、歌词创作等多种创作形式
