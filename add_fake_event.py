#!/usr/bin/env python3
"""
Modified add_fake_event.py that accepts an item ID as a parameter
"""

import os
import sys
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import glob
from datetime import datetime, timezone
import time
# Google Calendar API 的访问权限范围
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_calendar():
    """认证用户并返回 Google Calendar API 服务"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)

def clear_all_events(service):
    """清除主日历中的所有事件"""
    try:
        # 获取所有事件
        events_result = service.events().list(
            calendarId='primary',
            maxResults=2500,  # 最大返回数量
            showDeleted=False
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("Calendar is already empty.")
            return
        
        print(f"Found {len(events)} events in calendar. Deleting...")
        
        # 逐个删除事件
        deleted_count = 0
        for event in events:
            try:
                service.events().delete(calendarId='primary', eventId=event['id']).execute()
                deleted_count += 1
                if deleted_count % 10 == 0:
                    print(f"Deleted {deleted_count} events...")
            except HttpError as error:
                print(f"Error deleting event {event.get('summary', 'Untitled')}: {error}")
        
        print(f"Successfully deleted {deleted_count} events from calendar.")
        
    except HttpError as error:
        print(f'Error accessing calendar: {error}')
    except Exception as e:
        print(f'Unexpected error while clearing calendar: {e}')

def convert_event_format(event_data):
    """将原始格式转换为 Google Calendar API 格式"""
    converted_event = {
        'summary': event_data.get('summary', ''),
        'description': event_data.get('description', ''),
        'location': event_data.get('location', '')
    }
    
    # 转换开始时间
    if 'start' in event_data:
        converted_event['start'] = {
            'dateTime': event_data['start'],
            'timeZone': 'America/New_York'  # 或根据时间字符串自动解析时区
        }
    
    # 转换结束时间
    if 'end' in event_data:
        converted_event['end'] = {
            'dateTime': event_data['end'],
            'timeZone': 'America/New_York'  # 或根据时间字符串自动解析时区
        }
    
    # 转换参与者列表
    if 'attendees' in event_data and isinstance(event_data['attendees'], list):
        converted_event['attendees'] = []
        for attendee in event_data['attendees']:
            if isinstance(attendee, str):
                converted_event['attendees'].append({'email': attendee})
            elif isinstance(attendee, dict) and 'email' in attendee:
                converted_event['attendees'].append(attendee)
    
    return converted_event

def upload_calendar_event(service, json_path):
    """上传单个日历事件到 Google Calendar"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            event_data = json.load(f)

        # 转换数据格式
        converted_event = convert_event_format(event_data)
        
        # 创建事件
        event = service.events().insert(calendarId='primary', body=converted_event).execute()
        print(f"Successfully uploaded: {os.path.basename(json_path)} (ID: {event.get('id')})")
        return True
    except HttpError as error:
        print(f'Error uploading {os.path.basename(json_path)}: {error}')
        return False
    except json.JSONDecodeError as e:
        print(f'JSON decode error in {os.path.basename(json_path)}: {e}')
        return False
    except Exception as e:
        print(f'Unexpected error with {os.path.basename(json_path)}: {e}')
        return False

def upload_all_calendar_events(directory):
    """清空日历并上传指定目录中的所有 .json 日历事件文件"""
    service = authenticate_calendar()
    
    # 先清空日历
    print("Clearing calendar before upload...")
    clear_all_events(service)
    print()
    
    # 然后上传新事件
    json_files = glob.glob(os.path.join(directory, '*.json'))
    
    if not json_files:
        print(f"No .json files found in {directory}")
        return
    
    print(f"Found {len(json_files)} .json files to upload")
    successful = 0
    failed = 0
    
    for json_file in json_files:
        if "current_time.json" in json_file:
            print(f"Skipping {json_file}")
            continue
        
        print(f"Uploading {json_file}")
        if upload_calendar_event(service, json_file):
            successful += 1
        else:
            failed += 1
    
    print(f"\nUpload complete:")
    print(f"Successfully uploaded: {successful}")
    print(f"Failed to upload: {failed}")

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) != 2:
        print("Usage: python add_fake_event.py <item_id>")
        sys.exit(1)
    
    try:
        item_id = int(sys.argv[1])
    except ValueError:
        print("Error: Item ID must be an integer")
        sys.exit(1)
    
    # Construct the directory path based on the item ID
    directory = f'data/converted/item{item_id}'
    
    print(f"Processing item {item_id}")
    print(f"Directory: {directory}")
    
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)
    
    # Upload events from the directory
    upload_all_calendar_events(directory)

if __name__ == '__main__':
    main()