import random


class Person:
    def __init__(self, stats={}):
        if stats == {}:
            self.stats = {'fight_stats': {'hp': 0, 'armor': 0, 'damage': 0, 'aim': 0, 'mag': 0, 'max_mag': 0,
                                          'fire_mods': [], 'cur_mod': ''},
                          'stats': {'race_bonus': 0, 'streight': 0, 'intel': 0, 'motor': 0, 'speed': 0, 'name': ''}}
        else:
            self.stats = stats
        self.static_stats = stats
        self.bonuses = {}

    async def load_person(self, stats):
        self.stats = stats

    async def get_hurt(self, damage):
        self.stats['fight_stats']['hp'] = round((self.stats['fight_stats']['hp'] - damage), 2)

    async def get_info(self):
        info = str(self.stats["fight_stats"]["hp"]), str(self.stats["fight_stats"]["armor"]), \
               str(self.stats["fight_stats"]["damage"])
        return f'{self.stats["stats"]["name"]} [{" ".join(info)}]'

    async def get_fight_stats(self):
        return self.stats['fight_stats']

    async def get_static_fight_stats(self):
        mode_to_minimum = {'auto': 10, 'pew - pew': 3, 'semi': 1}
        hide_hp = self.static_stats['fight_stats']['hp'] - self.static_stats['fight_stats']['hp'] / 3
        heal_hp = self.static_stats['fight_stats']['hp'] - self.static_stats['fight_stats']['hp'] / 4
        mininmum_ammo_amount = mode_to_minimum[self.static_stats['fight_stats']['cur_mod']]
        armor = self.static_stats['fight_stats']['armor'] + self.static_stats['fight_stats']['armor'] * 0.03
        return hide_hp, heal_hp, armor, mininmum_ammo_amount

    async def get_stats(self):
        return self.stats['stats']

    async def reload(self):
        self.stats['fight_stats']['mag'] = self.stats['fight_stats']['max_mag']

    async def heal(self, heal):
        self.stats['fight_stats']['hp'] = round((self.stats['fight_stats']['hp'] + heal), 2)

    async def shoot(self, amount):
        self.stats['fight_stats']['mag'] -= amount

    async def change_mode(self):
        avalible_mods = self.stats['fight_stats']['fire_mods']
        cur_mod = self.stats['fight_stats']['cur_mod']
        if avalible_mods.index(cur_mod) + 1 >= len(avalible_mods):
            cur_mod = avalible_mods[0]
        else:
            cur_mod = avalible_mods[avalible_mods.index(cur_mod) + 1]
        self.stats['fight_stats']['cur_mod'] = cur_mod
        return cur_mod

    async def add_get_clear_bonus(self, *args):
        to_do = args[0]
        if len(args) > 1:
            name = args[1]
            if to_do == 'add':
                num = args[2]
                if name in self.bonuses:
                    self.bonuses[name] += num
                else:
                    self.bonuses[name] = num
            if to_do == 'clear':
                if name in self.bonuses:
                    self.bonuses[name] = 0
        elif to_do == 'get':
            return self.bonuses
