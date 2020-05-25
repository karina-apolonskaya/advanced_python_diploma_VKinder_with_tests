import requests
from datetime import datetime
import pprint
import json
from pymongo import MongoClient


class User:

    def __init__(self, user_id):
        self.user_id = user_id
        self.access_token = ""

    def generate_token(self):
        APP_ID = ""
        authorization = "https://oauth.vk.com/authorize?client_id=" + APP_ID + \
                        "&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=friends&" \
                        "response_type=token&v=5.52"
        print(f"Пройдите по ссылке {authorization} и скопируйте access_token!")
        TOKEN = input("Введите access_token: ")
        return TOKEN

    def convert_screenname_to_id(self, user_id):
        response = requests.get(
            "https://api.vk.com/method/utils.resolveScreenName",
            params={"access_token": self.access_token,
                 "v": "5.103",
                 "screen_name": user_id
                    }
        )
        info = response.json()["response"]
        USER_ID = info["object_id"]
        return USER_ID

    def get_user_info(self):
        params = {"access_token": self.access_token, "user_ids": self.convert_screenname_to_id(self.user_id),
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
            params = {"access_token": self.access_token, "country_id": 1, "q": city, "v": "5.103"}
            city_response = requests.get("https://api.vk.com/method/database.getCities", params=params).json()["response"]
            city_info = city_response["items"][0]
            response["city"] = city_info
        return response

    def search_users_by_sex_city_age_status(self):
        searched_users_collection = self.connect_to_Mongo()
        target_person = self.get_user_info()
        check_user_existance_lst = list()
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
            params={"access_token": self.access_token,
                    "v": "5.103",
                    "sex": users_sex,
                    "count": 1000,
                    "fields": "relation",
                    "has_photo": 1,
                    "city": users_city,
                    "age_from": start_age,
                    "age_to": start_age + 5
                    }
        )
        info = response.json()["response"]
        searched_users = info["items"]
        for user in searched_users:
            user_id = user["id"]
            user["link"] = f"https://vk.com/id{user_id}"
        relation_lst = [0, 1, 5, 6]
        check_user_existance = list(searched_users_collection.find({}, {"id": 1}))
        for element in check_user_existance:
            check_user_existance_lst.append(element["id"])
        for index in range(len(searched_users)-1, -1, -1):
            if searched_users[index]["id"] in check_user_existance_lst:
                searched_users.remove(searched_users[index])
            try:
                if searched_users[index]["relation"] not in relation_lst:
                    searched_users.remove(searched_users[index])
            except KeyError:
                continue
        return searched_users[:10]

    def get_3_popular_photos(self):
        searched_users = self.search_users_by_sex_city_age_status()
        searched_photos_lst = list()
        searched_photos_dict = dict()
        likes_link_lst = list()
        url_lst = list()
        for searched_user in searched_users:
            user_id = searched_user["id"]
            try:
                response = requests.get(
                    "https://api.vk.com/method/photos.get",
                    params={"access_token": self.access_token,
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
                                likes_link_lst.append({"likes": likes_count, "url": element["url"]})
                        searched_photos_dict[owner_id] = likes_link_lst
                    likes_link_lst = []
            except KeyError:
                continue
            for person in searched_photos_dict:
                for_sort = searched_photos_dict[person]
                for_sort.sort(key=lambda for_sort: for_sort['likes'], reverse=True)
                searched_photos_dict[person] = for_sort[:3]
                for el in for_sort[:3]:
                    url_lst.append(el["url"])
                searched_photos_dict[person] = url_lst
                searched_user["photos"] = url_lst
                url_lst = list()
        for item in searched_users:
            item.pop("is_closed")
            item.pop("track_code")
            item.pop("can_access_closed")
            try:
                item.pop("relation")
            except KeyError:
                continue
        return searched_users

    def create_json_file(self):
        with open("searched_users.json", "w", encoding='utf-8') as f:
            data = self.get_3_popular_photos()
            f.write(json.dumps(data, indent=1, ensure_ascii=False))
        return data

    def connect_to_Mongo(self):
        client = MongoClient("localhost", 27017)
        searched_users_db = client["searched_users"]
        searched_users_collection = searched_users_db['searched_user']
        return searched_users_collection

    def write_result_in_database(self):
        searched_users_collection = self.connect_to_Mongo()
        searched_users = self.create_json_file()
        for user in searched_users:
            searched_users_collection.insert_one(user)
        return searched_users_collection


if __name__ == '__main__':
    user_1 = User("")
    # TOKEN = user_1.generate_token()
    pprint.pprint(user_1.write_result_in_database())

