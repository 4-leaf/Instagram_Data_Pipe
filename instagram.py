from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
from sys import exit

class InstagramPipe:
    def __init__(self, page_id, token): | https://developers.facebook.com/docs/instagram-api/getting-started/
        self.page_id = page_id
        self.token = token
        self.global_post_ids = []
    
    def get_recent_posts(self):
        #https://graph.facebook.com/v3.2/17841401382913566/media?access_token={}
        """
        for IG PAGE
        Get the most recent 24 posts on an FB Page
        """
        posts_on_page = requests.get("https://graph.facebook.com/v3.2/{}/media?access_token={}".format(self.page_id, self.token))
        parsed_output = BeautifulSoup(posts_on_page.text, "html.parser")
        json_data = json.loads(parsed_output.get_text())
        return json_data
    
    def get_posts_ids(self, posts):
        """
        for IG PAGE
        Get the ID's of all POSTS on a IG Page
        """
        posts_ids = []
        for ids in posts['data']:
            posts_ids.append(ids['id'])
        return posts_ids
        
    def get_all_post_ids(self, list_of_ids, index, next_page):
        """
        for FB Page
        Get all post ID's recurrsively. This function will add List's to the GLOBAL List
        ''self.global_post_ids''
        this will then be used by other functions
        """
        if index == 1:
            posts_on_page = requests.get("https://graph.facebook.com/v3.2/{}/media?access_token={}".format(self.page_id, self.token))
            parsed_output = BeautifulSoup(posts_on_page.text, "html.parser")
            json_data = json.loads(parsed_output.get_text())
            list_of_ids.append(self.get_posts_ids(json_data))
            next_page = self._next_page_url(json_data)
            self.get_all_post_ids(list_of_ids, 2, next_page)
        else:
            posts_on_page = requests.get(next_page)
            parsed_output = BeautifulSoup(posts_on_page.text, "html.parser")
            json_data = json.loads(parsed_output.get_text())
            list_of_ids.append(self.get_posts_ids(json_data))
            page_recursive = self._next_page_url(json_data)
            try:
                paging = json_data['paging']['next']
                self.get_all_post_ids(list_of_ids,2, page_recursive)
            except(IndexError, KeyError):
                self.global_post_ids = list_of_ids
                return

    def _next_page_url(self, json_data):
        if json_data.get('paging'):
            return json_data['paging']['next']
        elif json_data.get('error'):
            exit("Key not valid?")

    def print_ids(self):
        for array in self.global_post_ids:
            for id in array:
                print(id)
    
    def get_post_date(self, post_id):
        """
        for IG POST
        Return Post Media Type
        """
        post_created = requests.get("https://graph.facebook.com/{}?fields=timestamp&access_token={}".format(post_id, self.token))
        parsed_output = BeautifulSoup(post_created.text, "html.parser")
        json_data = json.loads(parsed_output.get_text())
        try:
            date = json_data['timestamp'].split('T')
            return date[0]
        except(KeyError):
            return 0
    
    def get_post_media_type(self, post_id):
        """
        for IG POST
        Return Post Media Type
        """
        post_created = requests.get("https://graph.facebook.com/{}?fields=media_type&access_token={}".format(post_id, self.token))
        parsed_output = BeautifulSoup(post_created.text, "html.parser")
        json_data = json.loads(parsed_output.get_text())
        return json_data['media_type']
    
    def get_post_metrics(self, post_id):
        """
        for IG POST
        Return Post Metrics
        """
        # rewrite function to do video views as seperate function and refactor
        post_created = requests.get("https://graph.facebook.com/{}/insights?metric=impressions,reach&access_token={}".format(post_id, self.token))             
        parsed_output = BeautifulSoup(post_created.text, "html.parser")
        json_data = json.loads(parsed_output.get_text())
        
        impressions = json_data['data'][0]['values'][0]['value']
        reach = json_data['data'][1]['values'][0]['value']
        video_views = self.get_video_views(post_id)
        return [impressions, reach, video_views]
    
    def get_video_views(self, post_id):
        if self.get_post_media_type(post_id) == "VIDEO":
            post_created = requests.get("https://graph.facebook.com/{}/insights?metric=video_views&access_token={}".format(post_id, self.token))
            parsed_output = BeautifulSoup(post_created.text, "html.parser")
            json_data = json.loads(parsed_output.get_text())
            video_views = json_data['data'][0]['values'][0]['value']
        else:
            video_views = 0
        return video_views

    def get_post_by_date(self, date):
        output_list = []
        end_date = date.split("-")

        for arrays in self.global_post_ids:
            for post_id in arrays:
                post_date = self.get_post_date(post_id).split("-")
                if  datetime(int(post_date[0]), int(post_date[1]), int(post_date[2])) >=  datetime(int(end_date[0]), int(end_date[1]), int(end_date[2])):
                    output_list.append(post_id)
                else:
                    break
        print("found {} posts that match the timeframe for {}".format(len(output_list), date))
        return output_list
    
    def build_object(self, data):
        """
        Turns every ID in data into a JSON object using the methods above.
        saves to ''output_list''.
        """
        output_list = []
        for items in data:
            metrics = self.get_post_metrics(items)
            _object = {}
            _object['post_id'] = items
            _object['date'] = self.get_post_date(items)
            _object['media_type'] = self.get_post_media_type(items)
            _object['impressions'] = metrics[0]
            _object['reach'] = metrics[1]
            _object['video_views'] = metrics[2]
            json_data = json.dumps(_object)
            output_list.append(json_data)
            print("{} - spidered".format(items))
        return output_list


ig = InstagramPipe('', '')
ig.get_all_post_ids([], 1, "")
print(ig.build_object(ig.get_post_by_date("2019-06-01")))
