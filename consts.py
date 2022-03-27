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
# Группа названий кнопок расы
group_lbl_button_nation = ['Северяне', 'Южнане', 'Техно-гики']
# Группа названий кнопок происхождения
group_lbl_button_origin = ['Богатая семья', 'Обычная семья', 'Бедность']
# Имя чата регистрации
NAME_CHANNEL_REG = "создание-персонажа"
# Категории и их чаты
# non-game, game, all, city_topolis, city_braifast, city_jadiff
Objects = {
    "ОБЩЕЕ": {
        NAME_CHANNEL_REG: {"type": "non-game", "messaging": False, "position": 0},
        "информация": {"type": "game", "messaging": False, "position": 1},
        "магазин": {"type": "game", "messaging": False, "position": 2}
    },
    "Тополис": {
        "доска-объявлений-т": {"type": "city_topolis", "messaging": False, "position": 0},
        "таверна-т": {"type": "city_topolis", "messaging": True, "position": 1}
    },
    "Браифаст": {
        "доска-объявлений-б": {"type": "city_braifast", "messaging": False, "position": 0},
        "таверна-б": {"type": "city_braifast", "messaging": True, "position": 1}
    },
    "Джадифф": {
        "доска-объявлений-д": {"type": "city_jadiff", "messaging": False, "position": 0},
        "таверна-д": {"type": "city_jadiff", "messaging": True, "position": 1}
    }
}
# Роли
roles_game = ["Игрок", "Тополис", "Браифаст", "Джадифф"]

# Прочее
TOKEN = "NTY3MzMyNTU5NDc5MTExNzQw.XLR_ng.zhaxoAo_6ZL-LfA5gBEZXPAfGj0"
PREFIX = "/"
