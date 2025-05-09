import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API 的访问权限范围
SCOPES = ['https://www.googleapis.com/auth/gmail.insert']

def authenticate_gmail():
    """认证用户并返回 Gmail API 服务"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def upload_eml_file(service, eml_path):
    """上传 .eml 文件到 Gmail 收件箱"""
    with open(eml_path, 'rb') as f:
        raw_message = base64.urlsafe_b64encode(f.read()).decode()

    message = {'raw': raw_message, 'labelIds': ['INBOX']}
    try:
        uploaded_msg = service.users().messages().insert(userId='me', body=message).execute()
        print(f"Uploaded message ID: {uploaded_msg['id']}")
    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    service = authenticate_gmail()
    upload_eml_file(service, 'custom_mail.eml')
