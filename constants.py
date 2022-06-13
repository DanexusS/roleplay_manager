import json

from data import db_session

db_session.global_init("db/DataBase.db")

DB_SESSION = db_session.create_session()

TEST_GUILDS_ID = [936293335063232672]
PREFIX = "/"
TOKEN = "NTY3MzMyNTU5NDc5MTExNzQw.Gzvp-s.WpdYhbQXNxlKhUc53ARbLny9bpMDlb9JhNwc-k"

EMOJIS = {}

with open("json_data/localizations.json", encoding="utf8") as json_file:
    LOCALIZATIONS = json.load(json_file)
