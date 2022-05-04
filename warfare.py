import random


class Battle:
    def __init__(self):
        self.warriors = {'player': [], 'enemy': []}
        self.queue = 'Player'

    async def add_persons(self, persons):
        self.warriors['player'] = persons[0]
        self.warriors['enemy'] = persons[1]
        await self.turn()

    @staticmethod
    async def win_lose(win):
        if win:
            print('УраПобеда')
        else:
            print('____')
            print('Поражение')

    async def turn(self):
        od = 5
        more = True
        player = self.warriors['player'][0]
        print('___Ваш ход___')
        while od != 0:
            print('1 - attack, 2 - hide, 3 - reload, 4 - heal, 5 - change mode')
            print(od)
            choice = input()
            if choice == '1':
                for elem in self.warriors['enemy']:
                    print(f'{self.warriors["enemy"].index(elem) + 1}) {elem.get_info()}')
                choice = int(input())
                a = await self.attack(self.warriors['enemy'][choice - 1], player)
                if a > 0:
                    print(f'Вы нанесли урон в размере {a} hp')
                    if self.warriors['enemy'][choice - 1].get_fight_stats()['hp'] <= 0:
                        self.warriors['enemy'].remove(self.warriors['enemy'][choice - 1])
                        if len(self.warriors['enemy']) == 0:
                            await self.win_lose(True)
                            more = False
                            break
                else:
                    print('Вы не смогли нанести противнику урон')
                od -= 1
            elif choice == '2':
                choice = '1'
                while choice != '2' and od != 0:
                    a = await self.hide(player)
                    if a >= 0:
                        print(f'Вы спрятались, ваша защита стала {a} единиц')
                    else:
                        print('Вы не смогли спрятаться')
                    print('1) Сменить позицию')
                    print('2) Остаться')
                    od -= 1
                    choice = input()
            elif choice == '3':
                if self.warriors['player'][0].get_fight_stats()['mag'] == \
                        self.warriors['player'][0].get_fight_stats()['max_mag']:
                    print('Перезарядка не требуется')
                else:
                    base_motor = 15 + player.get_stats()['motor']
                    choice = '1'
                    while choice != '2' and od != 0:
                        a = random.randint(1, 100)
                        if a <= base_motor:
                            choice = '2'
                            player.reload()
                            print(player.get_fight_stats()['mag'])
                            print('Вы успешно перезарядили оружие')
                        else:
                            print('Вы не смогли перезарядить оружие')
                            print('1) Повторить попытку')
                            print('2) Оставить')
                            choice = input()
                        od -= 1

            elif choice == '4':
                heal = 15 + random.randint(1, player.get_stats()['intel'] // 2)
                print(f'Вы восполнили своё здоровье на {heal} hp')
                player.heal(heal)
                od -= 1
            elif choice == '5':
                print(player.change_mode())
        if more:
            print('___ход противника___')
        for elem in self.warriors['enemy']:
            print(f'__ {elem.get_stats()["name"]} __')
            od = 5
            warrior = elem
            heal_point, hide_point, armor_point, min_mag = warrior.get_static_fight_stats()
            while od >= 1:
                warrior_stats = warrior.get_fight_stats()
                if (warrior_stats['hp'] < hide_point and warrior_stats['armor'] >= armor_point) or \
                        warrior_stats['hp'] < heal_point:
                    heal = 4 + random.randint(1, warrior.get_stats()['intel'] // 2)
                    print(f'Противник восполнил своё здоровье на {heal} hp')
                    warrior.heal(heal)
                    od -= 1
                elif warrior_stats['hp'] < hide_point and warrior_stats['armor'] <= armor_point:
                    print('ща как сныкаюсь')
                    a = await self.hide(warrior)
                    if a >= 0:
                        print(f'Противник спрятался, его защита возросла на {a} единиц')
                    else:
                        print('Противник не смог спрятаться')
                    od -= 1
                elif warrior_stats['mag'] <= min_mag:
                    print('ПЕРЕЗАРЯЖАЮСЬ')
                    if warrior_stats['mag'] != warrior_stats['max_mag']:
                        base_motor = 15 + warrior.get_stats()['motor']
                        a = random.randint(1, 100)
                        if a <= base_motor:
                            warrior.reload()
                            print('Противник успешно перезарядил оружие')
                        else:
                            print('Противник не смог перезарядить оружие')
                        od -= 1
                else:
                    print('Пизда тебе капчёный')
                    dealed_damage = await self.attack(self.warriors['player'][0], warrior)
                    if dealed_damage > 0:
                        print(f'Вам нанесли урон в размере {dealed_damage} hp')
                        if player.get_fight_stats()['hp'] <= 0:
                            await self.win_lose(False)
                            more = False
                            break
                    od -= 1

            if not more:
                break
            print('____')
        if more:
            await self.turn()

    @staticmethod
    async def hide(warrior):
        base_speed = 15 + warrior.get_stats()['speed']
        arm_bonus = {'field': 0, 'tree': 15, 'rock': 20, 'baricade': 30}
        a = random.randint(1, 100)
        if a <= base_speed:
            hide = random.choice(('field', 'tree', 'rock', 'baricade'))
            warrior.add_get_clear_bonus('add', 'armor+', arm_bonus[hide])
            return arm_bonus[hide] + warrior.get_fight_stats()['armor']
        else:
            return 0

    @staticmethod
    async def attack(target, warrior):
        base_aim = 30
        fire_mode = warrior.get_fight_stats()['cur_mod']
        mag = warrior.get_fight_stats()['mag']
        play_damage = warrior.get_fight_stats()['damage']
        play_aim = warrior.get_fight_stats()['aim']
        en_armor = target.get_fight_stats()['armor']
        total_damage = 0
        if 'aim+' in warrior.add_get_clear_bonus('get'):
            base_aim += warrior.add_get_clear_bonus('get')['aim+']
        if fire_mode == 'semi' and mag >= 1:
            shoots = 1
            warrior.shoot(1)
        elif fire_mode == 'pew - pew' and mag >= 3:
            warrior.shoot(3)
            shoots = 3
            base_aim -= 20
        elif fire_mode == 'auto' and mag >= 10:
            warrior.shoot(10)
            shoots = 10
            base_aim -= 25
        else:
            print('Недостаточно патронов')
            shoots = 0
        for i in range(shoots):
            if random.randint(1, 100) <= base_aim + play_aim and play_damage > en_armor * 0.01:
                target.get_hurt(play_damage - en_armor * 0.01)
                warrior.add_get_clear_bonus('clear', 'aim+')
                total_damage += play_damage - en_armor * 0.01
            else:
                warrior.add_get_clear_bonus('add', 'aim+', 10)

        return total_damage


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



channel = await discord.utils.get(guild.text_channels, name="доска-объявлений-д")
            for elem in self.missions:
                await channel.send(f"**____**\n"
                                   f"{elem['descript']}\n"
                                   f"*ы*\n"
                                   f"᲼᲼____")