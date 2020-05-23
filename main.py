import requests
from datetime import datetime
import pprint
import json
from pymongo import MongoClient

TOKEN = " "
# пока прописываю токен здесь для отладки


class User:

    def __init__(self, user_id):
        self.user_id = user_id

    def generate_token(self):
        APP_ID = " "
        authorization = "https://oauth.vk.com/authorize?client_id=" + APP_ID + \
                        "&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=friends&" \
                        "response_type=token&v=5.52"
        print(f"Пройдите по ссылке {authorization} и скопируйте access_token!")
        TOKEN = input("Введите access_token: ")
        return TOKEN

    def convert_screenname_to_id(self, user_id):
        response = requests.get(
            "https://api.vk.com/method/utils.resolveScreenName",
            params={"access_token": TOKEN,
                 "v": "5.103",
                 "screen_name": user_id
                    }
        )
        info = response.json()["response"]
        USER_ID = info["object_id"]
        return USER_ID

    def get_user_info(self):
        params = {"access_token": TOKEN, "user_ids": self.convert_screenname_to_id(self.user_id),
                  "fields": "bdate, city, sex, relation", "v": "5.103"}
        response = requests.get("https://api.vk.com/method/users.get", params=params).json()['response'][0]
        if "bdate" not in response:
            bdate = input("Введите вашу дату рождения в формате дд.м.гггг: ")
            response["bdate"] = bdate
        if len(response["bdate"]) < 7:
            user_bdate_year = input("Введите ваш год рождения: ")
            full_bdate = response["bdate"] + "." + user_bdate_year
            response["bdate"] = full_bdate
        if "city" not in response:
            city = input("Введите ваш город: ")
            params = {"access_token": TOKEN, "country_id": 1, "q": city, "v": "5.103"}
            city_response = requests.get("https://api.vk.com/method/database.getCities", params=params).json()["response"]
            city_info = city_response["items"][0]
            response["city"] = city_info
        return response

    def search_users_by_sex_city_age_status(self):
        target_person = self.get_user_info()
        if target_person["sex"] == 1:
            users_sex = 2
        elif target_person["sex"] == 2:
            users_sex = 1
        city = target_person["city"]
        users_city = city["id"]
        target_person_bdate = datetime.strptime(target_person["bdate"], '%d.%m.%Y')
        date_now = datetime.now()
        start_age = date_now.year - target_person_bdate.year
        response = requests.get(
            "https://api.vk.com/method/users.search",
            params={"access_token": TOKEN,
                    "v": "5.103",
                    "sex": users_sex,
                    "count": 1000,
                    "fields": "has_photo, relation",
                    "city": users_city,
                    "age_from": start_age,
                    "age_to": start_age + 5
                    }
        )
        info = response.json()["response"]
        searched_users = info["items"]
        relation_lst = [0, 1, 5, 6]
        searched_users_lst = list()
        for user in searched_users:
            try:
                if user["has_photo"] == 1 and user["relation"] in relation_lst:
                    searched_users_lst.append(user)
            except KeyError:
                continue
        return searched_users_lst[:10]

    def get_3_popular_photos(self):
        searched_users = self.search_users_by_sex_city_age_status()
        searched_photos_lst = list()
        searched_photos_dict = dict()
        likes_link_lst = list()
        for user in searched_users:
            user_id = user["id"]
            response = requests.get(
                "https://api.vk.com/method/photos.get",
                params={"access_token": TOKEN,
                        "v": "5.103",
                        "owner_id": user_id,
                        "album_id": "profile",
                        "photo_sizes": 1,
                        "extended": 1
                        }
            )
            user_info = response.json()["response"]["items"]
            searched_photos_lst.append(user_info)
            for user in searched_photos_lst:
                for item in user:
                    owner_id = item["owner_id"]
                    likes_count = item["likes"]["count"]
                    sizes = item["sizes"]
                    for element in sizes:
                        if element["type"] == "x":
                            url = element["url"]
                            likes_link_dict = {"likes": likes_count, "url": url}
                            likes_link_lst.append(likes_link_dict)
                searched_photos_dict[owner_id] = likes_link_lst
                likes_link_lst = []
                user_likes_lst = list()
                user_likes_dict = dict()
                for user in searched_photos_dict:
                    for id_value in searched_photos_dict[user]:
                        user_likes = id_value["likes"]
                        user_likes_lst.append(user_likes)
                    user_likes_dict[user] = user_likes_lst
                    user_likes_lst = list()
                    user_url_lst = list()
                    final_dict = dict()
                for user_id in user_likes_dict:
                    if len(user_likes_dict) > 3:
                        sorted_likes_lst = sorted(user_likes_dict[user_id], reverse=True)
                        user_likes_dict[user_id] = sorted_likes_lst[:3]
                        for user in searched_photos_dict:
                            for id_value in searched_photos_dict[user]:
                                if user == user_id and id_value["likes"] in user_likes_dict[user_id]:
                                    user_url_lst.append(id_value["url"])
                                    final_dict[str(user)] = user_url_lst
                            user_url_lst = list()
        return final_dict

    def create_json_file(self):
        with open("searched_users.json", "w", encoding='utf-8') as f:
            data = self.get_3_popular_photos()
            f.write(json.dumps(data, ensure_ascii=False))

    def write_result_in_database(self):
        client = MongoClient()
        searched_users_db = client["searched_users"]
        searched_users_collection = searched_users_db['searched_user']
        searched_users = self.get_3_popular_photos()
        searched_users_collection.insert_one(searched_users)
        return searched_users_collection


if __name__ == '__main__':
    user_1 = User(" ")
    pprint.pprint(user_1.create_json_file())

