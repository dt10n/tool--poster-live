# -*- coding: utf-8 -*-
"""
飞书API集成模块
用于从飞书群和文档中抓取直播通告信息
"""
import requests
import json
import time

class FeishuAPI:
    def __init__(self, app_id, app_secret):
        """
        初始化飞书API
        :param app_id: 飞书应用ID
        :param app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_token = None
        self.token_expire = 0
    
    def get_token(self):
        """
        获取访问令牌
        """
        if time.time() < self.token_expire:
            return self.tenant_token
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        if result.get("code") == 0:
            self.tenant_token = result.get("tenant_access_token")
            self.token_expire = time.time() + result.get("expire", 0) - 300  # 提前5分钟刷新
            return self.tenant_token
        else:
            raise Exception(f"获取飞书token失败: {result.get('msg') or '未知错误'}")
    
    def get_chat_messages(self, chat_id, limit=50):
        """
        获取群聊消息（支持分页）
        :param chat_id: 群聊ID
        :param limit: 每页获取消息数量
        """
        tenant_token = self.get_token()
        
        all_messages = []
        page_token = None
        
        while True:
            url = f"https://open.feishu.cn/open-apis/im/v1/messages?container_id={chat_id}&container_id_type=chat&limit={limit}"
            if page_token:
                url += f"&page_token={page_token}"
            
            headers = {
                "Authorization": f"Bearer {tenant_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            
            try:
                result = response.json()
                
                if result.get("code") == 0:
                    items = result.get("data", {}).get("items", [])
                    all_messages.extend(items)
                    
                    # 获取下一页
                    page_token = result.get("data", {}).get("page_token")
                    if not page_token:
                        break
                else:
                    raise Exception(f"获取群聊消息失败: {result.get('msg') or '未知错误'}")
            except json.JSONDecodeError as e:
                raise Exception(f"获取群聊消息失败: JSON解析错误 - {e}")
        
        return all_messages
    
    def get_document_content(self, doc_token):
        """
        获取文档内容
        :param doc_token: 文档token
        """
        tenant_token = self.get_token()
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
        headers = {
            "Authorization": f"Bearer {tenant_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        
        try:
            result = response.json()
            
            if result.get("code") == 0:
                return result
            else:
                raise Exception(f"获取文档内容失败: {result.get('msg') or '未知错误'}")
        except json.JSONDecodeError as e:
            raise Exception(f"获取文档内容失败: JSON解析错误 - {e}")
    
    def download_image(self, image_key, output_path):
        """
        下载飞书图片
        :param image_key: 图片的image_key
        :param output_path: 保存路径
        """
        import urllib.parse
        
        tenant_token = self.get_token()
        
        # 飞书下载图片的正确 API
        url = f"https://open.feishu.cn/open-apis/im/v1/images/{urllib.parse.quote(image_key)}"
        headers = {
            "Authorization": f"Bearer {tenant_token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                # 获取图片的 download_url
                download_url = data.get("temporary_url")
                if download_url:
                    # 下载实际图片内容
                    img_response = requests.get(download_url)
                    if img_response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(img_response.content)
                        return True
            print(f"解析图片URL失败: {result}")
            return False
        else:
            print(f"下载图片失败: {response.status_code} - {response.text[:100]}")
            return False

if __name__ == "__main__":
    # 测试代码
    from config import FEISHU_CONFIG
    
    feishu = FeishuAPI(FEISHU_CONFIG['app_id'], FEISHU_CONFIG['app_secret'])
    
    # 测试获取token
    try:
        token = feishu.get_token()
        print(f"获取token成功: {token[:20]}...")
        
        # 测试获取群聊消息
        chat_id = FEISHU_CONFIG['group_chat_id']
        messages = feishu.get_chat_messages(chat_id, limit=5)
        print(f"获取群聊消息成功: {len(messages)}条消息")
        if messages:
            print(f"第一条消息: {messages[0].get('content', {})}")
    except Exception as e:
        print(f"测试失败: {e}")