import json

# id используемых эмодзи
emoji = {
    "rich": 955784319702548550,
    "norm": 955777557826002974,
    "poor": 955777604357603358,
    "north": 955784315449532456,
    "south": 955784858897104916,
    "techno": 955784858804842506,
    "money": 956604076739682304
}
# Эмодзи номера
numbers_emoji = {
    0: "0️",
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟"
}
# Группа названий кнопок расы
group_lbl_button_nation = ['Северяне', 'Южане', 'Техно-гики']
# Группа названий кнопок происхождения
group_lbl_button_origin = ['Богатая семья', 'Обычная семья', 'Бедность']
# Категории и их чаты
# types = non-game, game, all, city_topolis, city_braifast, city_jadiff, music
Objects = json.load(open("objects.json", encoding="utf8"))
# Роли
roles_game = ["Игрок", "Тополис", "Браифаст", "Джадифф"]

# Прочее
TOKEN = "NTY3MzMyNTU5NDc5MTExNzQw.XLR_ng.zhaxoAo_6ZL-LfA5gBEZXPAfGj0"
PREFIX = "/"
BOT_ID = 567332559479111740
