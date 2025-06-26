import os
import json
import time
import requests
import sys
import re
from datetime import datetime
import jsonschema
from jsonschema import validate

# 输入输出JSON Schema定义
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "theme": {"type": "string", "minLength": 2},
        "poem_style": {"type": "string", "enum": ["古诗", "现代诗", "自由体", "不限"]},
        "length": {"type": "integer", "minimum": 4, "maximum": 20}
    },
    "required": ["theme"]
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "theme": {"type": "string"},
        "comparisons": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "params": {"type": "string"},
                    "label": {"type": "string"},
                    "poem": {"type": "string"},
                    "analysis": {"type": "string"}
                },
                "required": ["params", "label", "poem"]
            }
        },
        "generated_at": {"type": "string"}
    },
    "required": ["theme", "comparisons"]
}

# 敏感词过滤列表
SENSITIVE_WORDS = ["暴力", "色情", "政治", "敏感词", "违禁", "非法", "反动"]

# 动画效果字符
ANIMATION_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

def validate_input(input_data):
    """使用JSON Schema验证输入数据"""
    try:
        validate(instance=input_data, schema=INPUT_SCHEMA)
        return True, ""
    except jsonschema.exceptions.ValidationError as e:
        return False, f"输入验证失败: {e.message}"

def validate_output(output_data):
    """使用JSON Schema验证输出数据"""
    try:
        validate(instance=output_data, schema=OUTPUT_SCHEMA)
        return True, ""
    except jsonschema.exceptions.ValidationError as e:
        return False, f"输出验证失败: {e.message}"

def filter_sensitive_words(text):
    """增强敏感词过滤函数"""
    for word in SENSITIVE_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        text = pattern.sub('***', text)
    return text

def prevent_prompt_injection(prompt):
    """防止指令注入攻击"""
    prompt = re.sub(r'[;\\/*]', '', prompt)
    return prompt[:1000]

def get_user_input():
    """获取用户输入"""
    print("\n" + "="*70)
    print("🎭 AI对话诗人 - 参数调优演示系统 🎭")
    print("="*70)
    
    print("\n请提供诗歌创作要求：")
    
    theme = input("1. 诗歌主题（例如：春天、离别、大海）: ").strip()
    if not theme:
        theme = "自然"
        print(f"⚠️ 未输入主题，使用默认主题: {theme}")
    
    styles = ["古诗", "现代诗", "自由体", "不限"]
    print("\n可选诗歌风格:")
    for i, style in enumerate(styles, 1):
        print(f"{i}. {style}")
    
    style_choice = input("选择诗歌风格 (1-4, 默认4): ").strip() or "4"
    try:
        style_idx = int(style_choice) - 1
        poem_style = styles[style_idx] if 0 <= style_idx < len(styles) else "不限"
    except ValueError:
        poem_style = "不限"
    
    length = input("诗歌行数 (4-20, 默认8): ").strip()
    try:
        length = int(length) if length else 8
        length = max(4, min(20, length))
    except ValueError:
        length = 8
    
    input_data = {
        "theme": theme,
        "poem_style": poem_style,
        "length": length
    }
    
    is_valid, error_msg = validate_input(input_data)
    if not is_valid:
        print(f"❌ {error_msg}")
        return get_user_input()
    
    return input_data

def animate_loading(message, duration=3):
    """显示加载动画"""
    start_time = time.time()
    i = 0
    
    while time.time() - start_time < duration:
        sys.stdout.write(f"\r{ANIMATION_CHARS[i % len(ANIMATION_CHARS)]} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    
    clear_spaces = " " * (len(message) + 10)
    sys.stdout.write("\r" + clear_spaces + "\r")
    sys.stdout.flush()

def generate_poem(input_data, temperature=0.7, top_p=0.9, max_tokens=500, stream=True, retry=3):
    """使用DeepSeek API生成诗歌"""
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": "Bearer sk-e70766d8965543979169182be06eab53",
        "Content-Type": "application/json"
    }
    
    style_instruction = {
        "古诗": "请创作一首符合格律的古诗",
        "现代诗": "请创作一首现代诗",
        "自由体": "请创作一首自由体诗歌",
        "不限": "请创作一首诗歌"
    }.get(input_data["poem_style"], "请创作一首诗歌")
    
    prompt_content = f"""
    你是一位富有诗意的AI诗人，请根据用户要求创作诗歌。
    创作要求：
    1. 主题：{input_data['theme']}
    2. {style_instruction}
    3. 诗歌长度：{input_data['length']}行
    4. 语言优美，富有意境
    
    注意：请确保内容积极健康，避免任何不当内容。
    """
    
    prompt_content = filter_sensitive_words(prompt_content)
    prompt_content = prevent_prompt_injection(prompt_content)
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位专业的诗人，擅长创作各种风格的诗歌。"},
            {"role": "user", "content": prompt_content}
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stream": stream
    }
    
    attempts = 0
    while attempts < retry:
        try:
            response = requests.post(
                API_URL, 
                headers=headers, 
                json=payload, 
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"\n🌼 参数组合 [温度={temperature}, top_p={top_p}] 创作中...\n")
                print(f"🎨 风格描述: {get_style_description(temperature, top_p)}\n")
                full_content = ""
                
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
                                            time.sleep(0.02)
                                except json.JSONDecodeError:
                                    continue
                
                print("\n" + "="*70 + "\n")
                return full_content
            else:
                attempts += 1
                print(f"⚠️ API请求失败，状态码: {response.status_code} (尝试 {attempts}/{retry})")
                time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            attempts += 1
            print(f"⚠️ 请求异常: {e} (尝试 {attempts}/{retry})")
            time.sleep(1)
    
    print(f"❌ 多次尝试后仍失败，跳过此参数组合")
    return None

def get_style_description(temperature, top_p):
    """根据参数获取风格描述"""
    if temperature < 0.5 and top_p < 0.7:
        return "严谨工整，主题集中（低随机性+高聚焦）"
    elif temperature < 0.5 and top_p >= 0.7:
        return "主题明确，语言规范（低随机性+高多样性）"
    elif temperature >= 0.5 and top_p < 0.7:
        return "创意丰富，表达新颖（高随机性+高聚焦）"
    else:
        return "自由奔放，富有想象力（高随机性+高多样性）"

def analyze_poem(poem):
    """分析诗歌特点"""
    if "，" in poem or "。" in poem or "：" in poem:
        return "这首诗歌采用了传统格式，注重韵律和节奏"
    elif len(poem.splitlines()) > 10:
        return "这是一首长诗，包含丰富意象和情感表达"
    else:
        return "这是一首简洁的诗歌，语言精炼意境深远"

def display_parameter_comparison(input_data):
    """展示不同参数组合下的诗歌创作效果"""
    param_combinations = [
        {"temperature": 0.3, "top_p": 0.5, "label": "保守创作 (低随机性)"},
        {"temperature": 0.3, "top_p": 0.9, "label": "聚焦核心 (低随机性+高多样性)"},
        {"temperature": 1.2, "top_p": 0.5, "label": "创意发散 (高随机性+聚焦)"},
        {"temperature": 1.2, "top_p": 0.95, "label": "自由创作 (高随机性)"}
    ]
    
    results = []
    success_count = 0
    
    print(f"\n{'='*70}")
    print(f"✨ 主题《{input_data['theme']}》诗歌创作 - 参数调优对比演示 ✨")
    print(f"📜 诗歌风格: {input_data['poem_style']}, 行数: {input_data['length']}")
    print(f"{'='*70}\n")
    
    for idx, params in enumerate(param_combinations):
        print(f"🔹 组合 {idx+1}/{len(param_combinations)}: {params['label']}")
        print(f"  温度: {params['temperature']}, top_p: {params['top_p']}")
        
        poem = generate_poem(
            input_data,
            temperature=params["temperature"],
            top_p=params["top_p"]
        )
        
        if poem:
            analysis = analyze_poem(poem)
            results.append({
                "params": f"温度={params['temperature']}, top_p={params['top_p']}",
                "label": params["label"],
                "poem": poem,
                "analysis": analysis
            })
            success_count += 1
            print(f"📝 分析: {analysis}")
        else:
            example_poem = generate_example_poem(input_data, params["temperature"], params["top_p"])
            analysis = analyze_poem(example_poem)
            results.append({
                "params": f"温度={params['temperature']}, top_p={params['top_p']}",
                "label": params["label"],
                "poem": example_poem,
                "analysis": analysis
            })
            print(f"⚠️ 使用示例诗歌替代参数组合: {params['label']}")
            print(f"📝 分析: {analysis}")
        
        if idx < len(param_combinations) - 1:
            print("\n" + "-"*70 + "\n")
    
    return results, success_count

def generate_example_poem(input_data, temperature, top_p):
    """生成示例诗歌"""
    theme = input_data["theme"]
    style = input_data["poem_style"]
    length = input_data["length"]
    
    if temperature < 0.5 and top_p < 0.7:
        return f"""
        【{theme}·严谨版】
        春风吹绿江南岸，花开满园映日红。
        柳絮轻扬如雪舞，燕语莺啼入画中。
        
        碧水潺潺绕村过，青山隐隐映晴空。
        万物复苏生机旺，人间四月正葱茏。
        """[:length*20]
    elif temperature < 0.5 and top_p >= 0.7:
        return f"""
        【{theme}·规范版】
        春天悄然而至，大地披上新装，
        花朵争相绽放，鸟儿欢快歌唱。
        
        微风轻抚面庞，带来温暖气息，
        阳光洒满大地，万物焕发生机。
        """[:length*20]
    elif temperature >= 0.5 and top_p < 0.7:
        return f"""
        【{theme}·创意版】
        春天是位画家，泼洒绿意于大地，
        用阳光的笔触，点染花朵的笑靥。
        
        微风是她的低语，唤醒沉睡的种子，
        细雨是她的泪珠，滋润干渴的泥土。
        """[:length*20]
    else:
        return f"""
        【{theme}·自由版】
        啊！春之女神舞动她的裙摆，
        万物在韵律中苏醒、绽放！
        
        冬的桎梏已被打破，
        生命在每一片新叶上歌唱！
        """[:length*20]

def save_results_to_json(results, input_data):
    """将结果保存为JSON文件"""
    filename = f"poetry_comparison_{input_data['theme']}.json"
    
    output_data = {
        "theme": input_data["theme"],
        "comparisons": results,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    is_valid, error_msg = validate_output(output_data)
    if not is_valid:
        print(f"❌ 输出验证失败: {error_msg}")
        return filename
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存到: {filename}")
    return filename

def main():
    """主函数"""
    start_time = time.time()
    
    # 用户交互模块
    user_input = get_user_input()
    
    # 核心处理模块
    animate_loading("正在初始化诗歌创作引擎...", 2)
    results, success_count = display_parameter_comparison(user_input)
    
    # 输出处理模块
    filename = save_results_to_json(results, user_input)
    
    # 完成统计
    elapsed_time = time.time() - start_time
    total_combinations = 4
    
    print("\n" + "="*70)
    print("🎉 演示完成！")
    print(f"⏱️ 总运行时间: {elapsed_time:.2f}秒")
    print(f"📝 成功生成: {success_count}/{total_combinations} 首诗歌")
    print(f"💾 结果文件: {filename}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 程序发生未预期错误: {str(e)}")
        print("建议：请检查网络连接或API密钥")