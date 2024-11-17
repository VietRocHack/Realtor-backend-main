import requests

class PinataService:
    def __init__(self, pinata_secret_key, pinata_jwt, pinata_gateway):
        self.secret_key = pinata_secret_key
        self.jwt = pinata_jwt
        self.gateway = pinata_gateway
        return
    
    def test_authentication(self):
        url = "https://api.pinata.cloud/data/testAuthentication"
        
        headers = {"Authorization": f"Bearer {self.jwt}"}
        response = requests.request("GET", url, headers=headers)

        print(response.text)
        return response.status_code == 200

    def list_files(self, cid=None):
        url = "https://api.pinata.cloud/v3/files"
        headers = {"Authorization": f"Bearer {self.jwt}"}
        querystring = {}
        if cid:
            querystring["cid"] = cid
        response = requests.request("GET", url, headers=headers)
        return response.json()

    def upload_file(self, file_name, file_binary):
        url = "https://uploads.pinata.cloud/v3/files"
        files = {
            'file': (file_name, file_binary, 'text/plain')
        }        

        headers = {
            "Authorization": f"Bearer {self.jwt}",
        }

        response = requests.post(url=url, headers=headers, files=files)
        return response.json()
    
    def create_group(self, group_name, is_public=False):
        payload = {"name": group_name, "is_public": is_public}
        headers = {
            "Authorization": f"Bearer {self.jwt}",
            "Content-Type": "application/json"
        }

        response = requests.post("https://api.pinata.cloud/v3/files/groups", headers=headers, json=payload)
        return response.json()

    def list_groups(self):
        url = "https://api.pinata.cloud/v3/files/groups"

        headers = {
            "Authorization": f"Bearer {self.jwt}",
        }

        response = requests.get(   url=url, headers=headers)
        return response.json()
    
    def upload_file_to_group(self, group_id, file_name, file_binary):
        url = "https://uploads.pinata.cloud/v3/files"
        files = {
            'file': (file_name, file_binary, 'text/plain')
        }
        headers = {
            "Authorization": f"Bearer {self.jwt}",
        }
        file = requests.post(url=url, headers=headers, files=files)
        print("File uploaded successfully.")
        print(file.json())
        
        group_upload_url = f"https://api.pinata.cloud/v3/files/groups/{group_id}/ids/{file.json().get('data').get('id')}"
        print(group_upload_url)

        response = requests.request("PUT", group_upload_url, headers=headers)

        return file.json().get('data').get('cid')
    
    def get_file_public(self, cid):
        headers = {
            "Authorization": f"Bearer {self.jwt}",
        }
        gateway_url = f"https://{self.gateway}/files/{cid}"
        try:
            response = requests.get(gateway_url, headers=headers)
            response.raise_for_status()  # Raise an error for HTTP issues
            print("File content retrieved successfully.")
            return response.content  # Return binary content
        except requests.exceptions.RequestException as e:
            print(f"Error fetching file content: {e}")
            return None