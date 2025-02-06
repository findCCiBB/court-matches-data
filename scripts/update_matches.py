import json
import os
from datetime import datetime, timezone, timedelta
import requests

def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def save_json_file(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {file_path}")
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

def update_match_status():
    current_file = 'data/matches/current.json'
    current_data = load_json_file(current_file)
    
    if not current_data:
        return
    
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')
    
    # 更新比赛状态
    if today in current_data['matches']:
        valid_matches = []  # 新增：用于存储验证通过的比赛
        for match in current_data['matches'][today]:
            # 新增：添加数据验证
            if not validate_match_data(match):
                print(f"Skipping invalid match: {match.get('id', 'Unknown')}")
                continue
                
            match_time = datetime.strptime(f"{today} {match['startTime']}", '%Y-%m-%d %H:%M')
            match_time = match_time.replace(tzinfo=timezone.utc)
            
            if now < match_time:
                match['status'] = '未开始'
            elif now < match_time + timedelta(hours=3):
                match['status'] = '进行中'
            else:
                match['status'] = '已结束'
                move_to_history(match, today)
            
            valid_matches.append(match)  # 新增：只添加验证通过的比赛
        
        # 新增：更新为验证通过的比赛列表
        current_data['matches'][today] = valid_matches
    
    # 更新最后更新时间
    current_data['lastUpdated'] = now.isoformat()
    
    # 保存更新后的数据
    save_json_file(current_data, current_file)

def move_to_history(match, date):
    month = date[:7]  # 获取年月 (YYYY-MM)
    history_file = f'data/matches/history/{month}.json'
    
    # 加载或创建历史数据文件
    history_data = load_json_file(history_file) or {"month": month, "matches": {}}
    
    # 确保日期键存在
    if date not in history_data['matches']:
        history_data['matches'][date] = []
    
    # 检查比赛是否已经存在于历史记录中
    match_exists = any(m['id'] == match['id'] for m in history_data['matches'][date])
    
    if not match_exists:
        history_data['matches'][date].append(match)
        save_json_file(history_data, history_file)
        print(f"Moved match {match['id']} to history")

def validate_match_data(match):
    """验证比赛数据的完整性"""
    # 必需字段
    required_fields = ['id', 'league', 'status', 'startTime', 'homeTeam', 'awayTeam', 'venue', 'broadcast']
    
    # 检查必需字段
    if not all(field in match for field in required_fields):
        missing_fields = [field for field in required_fields if field not in match]
        print(f"Match {match.get('id', 'Unknown')} missing required fields: {missing_fields}")
        return False
    
    # 检查队伍信息
    for team_type in ['homeTeam', 'awayTeam']:
        team = match[team_type]
        team_required_fields = ['id', 'name', 'logo']
        if not all(field in team for field in team_required_fields):
            print(f"Team {team.get('name', 'Unknown')} missing required fields")
            return False
    
    # 验证时间格式
    try:
        datetime.strptime(match['startTime'], '%H:%M')
    except ValueError:
        print(f"Invalid time format for match {match['id']}")
        return False
    
    # 验证状态值
    valid_statuses = ['未开始', '进行中', '已结束']
    if match['status'] not in valid_statuses:
        print(f"Invalid status for match {match['id']}: {match['status']}")
        return False
    
    return True

def main():
    try:
        update_match_status()
        print("Successfully updated match data")
    except Exception as e:
        print(f"Error updating match data: {e}")

if __name__ == '__main__':
    main()
