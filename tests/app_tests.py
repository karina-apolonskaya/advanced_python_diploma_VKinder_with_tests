import unittest
from app import User


class TestMainFunctions(unittest.TestCase):
    def setUp(self):
        self.user_1 = User("")
        self.user_id = ""

    def test_convert_screenname_to_id(self):
        result = self.user_1.convert_screenname_to_id(self.user_id)
        self.assertTrue(int(result))

    def test_users_bdate(self):
        result = self.user_1.get_user_info()
        self.assertGreater(len(result["bdate"]), 6)

    def test_find_duplicates_in_database(self):
        db_connect = self.user_1.connect_to_Mongo()
        check_user_existance_lst = list()
        check_user_existance = list(db_connect.find({}, {"id": 1}))
        for element in check_user_existance:
            check_user_existance_lst.append(element["id"])
        self.assertEqual(len(check_user_existance_lst), len(set(check_user_existance_lst)))

    def test_write_in_database(self):
        db_connect = self.user_1.connect_to_Mongo()
        check_user_existance = list(db_connect.find())
        self.user_1.write_result_in_database()
        db_connect_2 = self.user_1.connect_to_Mongo()
        check_user_existance_again = list(db_connect_2.find())
        self.assertGreater(len(check_user_existance_again), len(check_user_existance))


if __name__ == '__main__':
    unittest.main()