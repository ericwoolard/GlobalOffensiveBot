# System imports
import requests
import requests.auth
# Third party imports
import praw
# Our imports
from file_manager import read, read_json, save_json

config = read_json('settings.json')


class Reddit:
    def __init__(self, stylesheet=None):
        self.user_agent = config['GlobalOffensiveBot']['user_agent']
        self.client_id = config['GlobalOffensiveBot']['client_id']
        self.client_secret = config['GlobalOffensiveBot']['client_secret']
        self.username = config['GlobalOffensiveBot']['username']
        self.password = config['GlobalOffensiveBot']['password']
        self.subreddit = config['GlobalOffensiveBot']['subreddit']
        self.r = self.get_praw_instance()

        # Temporary instance variables due to no PRAW support
        # for adding/editing widgets at the time of writing
        self.access_token = self.get_access_token()
        self.oauth_headers = {"Authorization": "bearer {}".format(self.access_token), "User-Agent": self.user_agent}
        self.widget_name = config['widget']['name']
        self.all_widgets_endpoint = 'https://oauth.reddit.com/r/{}/api/widgets'.format(self.subreddit)
        self.widget_id, self.widget_image_data = self.get_widget_info()
        self.widget_endpoint = 'https://oauth.reddit.com/r/{}/api/widget/{}'.format(self.subreddit, self.widget_id)
        self.widget_images_s3 = 'https://oauth.reddit.com/r/{}/api/widget_image_upload_s3'.format(self.subreddit)
        self.widget_markdown = ''
        if stylesheet is None:
            self.stylesheet = read('app-cache/strafe_widget_css.txt')
        else:
            self.stylesheet = stylesheet
        self.widget_height = config['widget']['height']
        self.widget_kind = config['widget']['kind']
        self.widget_styles = config['widget']['styles']
        self.live_placeholder = config['widget']['placeholders']['live']
        self.past_placeholder = config['widget']['placeholders']['past']

    def get_praw_instance(self):
        r = praw.Reddit(user_agent=self.user_agent,
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        username=self.username,
                        password=self.password)
        return r

    def get_access_token(self):
        client_auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        post_data = {"grant_type": "password", "username": self.username, "password": self.password}
        req_headers = {"User-Agent": self.user_agent}

        response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=req_headers).json()

        return response['access_token']

    def get_widget_info(self):
        widgets = requests.get(self.all_widgets_endpoint, headers=self.oauth_headers).json()
        for widget in widgets['items'].items():
            if 'shortName' in widget[1]:
                if widget[1]['shortName'] == self.widget_name:
                    config['widget']['id'] = widget[1]['id']
                    save_json('settings.json', config)
                    return widget[1]['id'], widget[1]['imageData']
        return None, None

    def upload_widget(self):
        if self.widget_id is None and self.widget_image_data is None:
            if self.widget_markdown != '':
                self.widget_image_upload()
                widget_data = {
                    "css": self.stylesheet,
                    "height": self.widget_height,
                    "imageData": config['widget']['images'],
                    "kind": self.widget_kind,
                    "shortName": self.widget_name,
                    "styles": {
                        "backgroundColor": self.widget_styles['backgroundColor'],
                        "headerColor": self.widget_styles['headerColor'],
                    },
                    "text": self.widget_markdown
                }
                widget = requests.post(self.widget_endpoint, json=widget_data, headers=self.oauth_headers)
                return widget
        elif self.widget_id is not None and self.widget_image_data is not None:
            return self.update_widget()

    def update_widget(self):
        if self.widget_markdown != '':
            widget_data = {
                "css": self.stylesheet,
                "height": self.widget_height,
                "imageData": self.widget_image_data,
                "kind": self.widget_kind,
                "shortName": self.widget_name,
                "styles": {
                    "backgroundColor": self.widget_styles['backgroundColor'],
                    "headerColor": self.widget_styles['headerColor'],
                },
                "text": self.widget_markdown
            }
            widget = requests.put(self.widget_endpoint, json=widget_data, headers=self.oauth_headers)
            return widget

    def widget_image_upload(self):
        # This method is incomplete. Fuck this shit.
        # TODO: Figure out why the bumfuck temporary S3 bucket lease won't
        # accept our POST for custom widget creation
        new_image_data = config['widget']['images']
        params = {
            "filepath": new_image_data[0]['url'],
            "mimetype": "image/{}".format(new_image_data[0]['url'].split('.')[1])
        }
        # aws_lease = requests.post(self.widget_images_s3, data=params, headers=self.oauth_headers).json()
        # fields = aws_lease['fields']
        # file = {'file': open('images/header.png', 'rb')}
        
        # response = requests.post('https:{}'.format(aws_lease['action']), data=fields, files=file)
        # print(response)

    def delete_widget(self):
        if self.widget_id is not None:
            delete = requests.delete(url=self.widget_endpoint, data=self.widget_id)
            if delete.status_code == 200:
                config['tournament_name'] = ''
