import time

from warfare import Battle, Person
import random
import json


class CreateBattle:
    def __init__(self, dif):
        self.difficulty = dif
        self.names = ['Лёха', 'Андрюха', 'Виталя', 'Жека', 'Гена', 'Влад', 'Дима', 'Юра', 'Олег', 'Миша', 'Ден', 'Макс',
                      'Вова', 'Арсюха', 'Марк', 'Тарас', 'Колян', 'Даня', 'Паша', 'Лёня', 'Кирилл', 'Ян', 'Денис']
        self.sir_names = ['Хмырь', 'Бульдозер', 'Шустрый', 'Фольга', 'Вобла', 'Татарин', 'Цыган', 'Колдун', 'Борода',
                          'Фин', 'Шаман', 'Бестолочь', 'Южанин', 'Бочка', 'Сокол', 'Батон', 'Чёрт', 'Чугун', 'Воробей',
                          'Химик', 'Крот', 'Бастард', 'Окурок', 'Ясень', 'Токарь', 'Кувалда', 'Шпала', 'Рябой',
                          'Копатель']

    async def create_buddies(self):
        name = f'{random.choice(self.names)} {random.choice(self.sir_names)}'
        mag_cap = random.choice([5, 15, 30, 60])
        fire_mods = ['semi']
        if mag_cap == 15:
            fire_mods.append('pew - pew')
        if mag_cap >= 30:
            fire_mods.append('auto')
        if self.difficulty == 1:
            return {'fight_stats': {'hp': random.randint(20, 40), 'armor': random.randint(5, 15),
                                    'damage': random.randint(7, 15), 'aim': random.randint(5, 14), 'mag': mag_cap,
                                    'max_mag': mag_cap, 'fire_mods': fire_mods, 'cur_mod': random.choice(fire_mods)},
                    'stats': {'race_bonus': 0, 'streight': random.randint(5, 10), 'intel': random.randint(5, 10),
                              'motor': random.randint(5, 10), 'speed': random.randint(5, 10), 'name': name}}
        elif self.difficulty == 2:
            return {'fight_stats': {'hp': random.randint(30, 60), 'armor': random.randint(10, 35),
                                    'damage': random.randint(14, 30), 'aim': random.randint(10, 18), 'mag': mag_cap,
                                    'max_mag': mag_cap, 'fire_mods': fire_mods, 'cur_mod': random.choice(fire_mods)},
                    'stats': {'race_bonus': 0, 'streight': random.randint(10, 17), 'intel': random.randint(10, 17),
                              'motor': random.randint(10, 17), 'speed': random.randint(10, 17), 'name': name}}
        elif self.difficulty == 3:
            return {'fight_stats': {'hp': random.randint(40, 80), 'armor': random.randint(25, 60),
                                    'damage': random.randint(20, 45), 'aim': random.randint(20, 29), 'mag': mag_cap,
                                    'max_mag': mag_cap, 'fire_mods': fire_mods, 'cur_mod': random.choice(fire_mods)},
                    'stats': {'race_bonus': 0, 'streight': random.randint(20, 30), 'intel': random.randint(20, 34),
                              'motor': random.randint(30, 50), 'speed': random.randint(30, 40), 'name': name}}

    async def start_battle(self):
        enemy = []
        dif_to_count = {1: (1, 5), 2: (2, 4), 3: (1, 3)}
        diap = dif_to_count[self.difficulty]
        for i in range(random.randint(diap[0], diap[1])):
            enemy.append(Person(self.create_buddies()))
        channel = await guild.create_text_channel(title, category=category, position=pos)
        start = Battle()
        await start.add_persons([[Person(dil)], enemy])


class TownMissions:
    def __init__(self, amount):
        self.missions = []
        self.amount = amount
        self.aim = {'find_him': 'Найти и уничожить', 'stolen_item': 'Вернуть украденную вешь владельцу',
                    'foreign territory': 'Уничтожить отряд противника',
                    'old_tech': 'Разведать обозначенную учёными местность'}
        self.scenario_to_dif = {'find_him': False, 'stolen_item': False, 'foreign territory': True, 'caravan': False,
                                'old_tech': True}

    async def add_missions(self):
        with open('scenarios.json', encoding="utf8") as scenarios:
            req = json.load(scenarios)
            scenario = req['missions']
            items = req['items']
        for i in range(self.amount):
            scen = random.choice(list(scenario.keys()))
            diff = random.randint(1, 3)
            if scen != 'stolen_item':
                if self.scenario_to_dif[scen]:
                    diff = 3
                self.missions.append(
                    {'time': random.randint(1, 60), 'difficulty': diff, 'descript': random.choice(scenario[scen]),
                     'aim': self.aim[scen]})
            else:
                line = random.choice(scenario[scen])
                line = line.replace('item', random.choice(items))
                self.missions.append(
                    {'time': random.randint(1, 60), 'difficulty': diff, 'descript': line,
                     'aim': self.aim[scen]})
        await self.show_mission()

    async def show_mission(self):
        for elem in self.missions:
            print('____')
            print(elem['descript'])
            print(f'Цель: {elem["aim"]}')


dil = {'fight_stats': {'hp': 4000, 'armor': 15, 'damage': 7, 'aim': 7, 'mag': 10, 'max_mag': 15,
       'fire_mods': ['semi', 'pew - pew', 'auto'], 'cur_mod': 'semi'},
       'stats': {'race_bonus': 15, 'streight': 10, 'intel': 9, 'motor': 20, 'speed': 7, 'name': 'tester'}}
a = TownMissions(10)
a.add_missions()
