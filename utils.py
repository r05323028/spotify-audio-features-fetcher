import requests
import ast
import settings

class Token:

    def __init__(self):
        self.response = None

    @classmethod    
    def get_token(cls):
        response = requests.post(
            settings.AUTH_URL, 
            data = settings.BODY_PARAMS, 
            auth = (settings.CLIENT_ID, settings.CLIENT_SECRET)
            )
        response = ast.literal_eval(response.text)
        return response