from data import db_session
from data.users import User
from data.items import Items

from functions import *
from custom_exceptions import *

db_session.global_init(f"db/DataBase.db")
db_sess = db_session.create_session()

TEST_GUILDS_ID = [936293335063232672]
PREFIX = "/"
TOKEN = "NTY3MzMyNTU5NDc5MTExNzQw.Gzvp-s.WpdYhbQXNxlKhUc53ARbLny9bpMDlb9JhNwc-k"

EMOJIS_ID = {
    "Богатая семья": 955784319702548550,
    "Обычная семья": 955777557826002974,
    "Бедная семья": 955777604357603358,
    "Северяне": 955784315449532456,
    "Южане": 955784858897104916,
    "Техно-гики": 955784858804842506,
    "Валюта": 956604076739682304
}
