#!/usr/bin/env python3
"""
飞书妙记获取工具
功能：获取妙记的文字记录
"""
import requests
# ============== 配置 ==============
USER_TOKEN = "u-dsDwouGNF5NofiY8TjtAIl10lyjghlghW0GaZwU024o6"
# 妙记 minute_token（从妙记链接中获取）
# 例如: https://jcneyh7qlo8i.feishu.cn/minutes/obcnb4r7575w2m39416cvaj3
# minute_token 就是: obcnb4r7575w2m39416cvaj3
MINUTE_TOKEN = "obcnb4r7575w2m39416cvaj3"
# ============== 工具函数 ==============
def get_minutes_transcript(token, minute_token):
    """
    获取妙记的文字记录
    """
    url = f"https://open.feishu.cn/open-apis/minutes/v1/minutes/{minute_token}/transcript"
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = requests.get(url, headers=headers)
    
    resp.encoding = 'utf-8'  # 关键！指定编码
    
    print("状态码:", resp.status_code)
    print("返回内容:", resp.text[:1000])  # 打印前500字符
    # result = resp.json()
    print(resp.text)
    if resp.status_code == 200:
        return resp.text  # 直接返回文本
    else:
        raise Exception(f"请求失败: {resp.status_code}")
    
    # if result.get("code") == 0:
    #     return result
    # else:
    #     raise Exception(f"获取妙记失败: {result}")
def format_transcript(result):
    """格式化输出妙记文字记录"""
    data = result.get("data", {})
    transcript = data.get("transcript", {})
    
    info = transcript.get("info", {})
    duration = info.get("duration", "")
    start_time = info.get("start_time", "")
    
    contents = transcript.get("contents", [])
    
    output = []
    output.append("=" * 60)
    output.append(f"妙记信息")
    output.append(f"  时长: {duration}")
    output.append(f"  开始时间: {start_time}")
    output.append("=" * 60)
    output.append("")
    
    for item in contents:
        speaker = item.get("speaker", "未知")
        text = item.get("text", "")
        time_offset = item.get("time_offset", 0)
        
        minutes = time_offset // 60
        seconds = time_offset % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        output.append(f"[{time_str}] {speaker}:")
        output.append(f"  {text}")
        output.append("")
    
    return "".join(output)
def save_to_file(content, filename="transcript.txt"):
    """保存到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已保存到 {filename}")
# ============== 主程序 ==============
if __name__ == "__main__":
    print("=" * 60)
    print("飞书妙记获取工具")
    print("=" * 60)
    
    token = USER_TOKEN
    minute_token = MINUTE_TOKEN
    
    print(f"[1] 获取妙记文字记录...")
    print(f"    minute_token: {minute_token}")
    
    try:
        result = get_minutes_transcript(token, minute_token)
        
        # data = result.get("data", {})
        # transcript = data.get("transcript", {})
        
        # info = transcript.get("info", {})
        print(f"✅ 获取成功！")
        # print(f"    时长: {info.get('duration', 'N/A')}")
        # print(f"    开始时间: {info.get('start_time', 'N/A')}")
        
        save_to_file(result, "transcript.txt")
        
        
        
    except Exception as e:
        print(f"    ❌ {e}")
    