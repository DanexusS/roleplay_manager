# import asyncio
# import random
# from pafy import new as make_new_video
# from datetime import datetime
#
# from nextcord.ext import commands
# from nextcord import Interaction, FFmpegPCMAudio, SlashOption
# from nextcord.utils import get
#
# from constants import *
# from cogs.trade import add_item
#
#
# BATTLES_ID = {}
#
#
# class Person:
#     def __init__(self, stats=None):
#         if not stats:
#             self.stats = {'fight_stats': {'hp': 0, 'armor': 0, 'damage': 0, 'aim': 0, 'mag': 0, 'max_mag': 0,
#                                           'fire_mods': [], 'cur_mod': ''},
#                           'stats': {'race_bonus': 0, 'streight': 0, 'intel': 0, 'motor': 0, 'speed': 0, 'name': ''}}
#         else:
#             self.stats = stats
#         self.static_stats = stats
#         self.bonuses = {}
#
#     async def load_person(self, stats):
#         self.stats = stats
#
#     async def get_hurt(self, damage):
#         self.stats['fight_stats']['hp'] = round((self.stats['fight_stats']['hp'] - damage), 2)
#
#     async def get_info(self):
#         info = str(self.stats["fight_stats"]["hp"]), str(self.stats["fight_stats"]["armor"]), \
#                str(self.stats["fight_stats"]["damage"])
#         return self.stats["stats"]["name"], info
#
#     async def get_fight_stats(self):
#         return self.stats['fight_stats']
#
#     async def get_static_fight_stats(self):
#         mode_to_minimum = {'auto': 10, 'pew - pew': 3, 'semi': 1}
#         hide_hp = self.static_stats['fight_stats']['hp'] - self.static_stats['fight_stats']['hp'] / 3
#         heal_hp = self.static_stats['fight_stats']['hp'] - self.static_stats['fight_stats']['hp'] / 4
#         mininmum_ammo_amount = mode_to_minimum[self.static_stats['fight_stats']['cur_mod']]
#         armor = self.static_stats['fight_stats']['armor'] + self.static_stats['fight_stats']['armor'] * 0.03
#         return hide_hp, heal_hp, armor, mininmum_ammo_amount
#
#     async def get_stats(self):
#         return self.stats['stats']
#
#     async def reload(self):
#         self.stats['fight_stats']['mag'] = self.stats['fight_stats']['max_mag']
#
#     async def heal(self, heal):
#         self.stats['fight_stats']['hp'] = round((self.stats['fight_stats']['hp'] + heal), 2)
#
#     async def shoot(self, amount):
#         self.stats['fight_stats']['mag'] -= amount
#
#     async def change_mode(self):
#         avalible_mods = self.stats['fight_stats']['fire_mods']
#         cur_mod = self.stats['fight_stats']['cur_mod']
#         if avalible_mods.index(cur_mod) + 1 >= len(avalible_mods):
#             cur_mod = avalible_mods[0]
#         else:
#             cur_mod = avalible_mods[avalible_mods.index(cur_mod) + 1]
#         self.stats['fight_stats']['cur_mod'] = cur_mod
#         return cur_mod
#
#     async def add_get_clear_bonus(self, *args):
#         to_do = args[0]
#         if len(args) > 1:
#             name = args[1]
#             if to_do == 'add':
#                 num = args[2]
#                 if name in self.bonuses:
#                     self.bonuses[name] += num
#                 else:
#                     self.bonuses[name] = num
#             if to_do == 'clear':
#                 if name in self.bonuses:
#                     self.bonuses[name] = 0
#         elif to_do == 'get':
#             return self.bonuses
#
#
# class TownMissions:
#     def __init__(self, amount, bot):
#         self.bot = bot
#         self.missions = []
#         self.town_letters = ['т', 'б', 'д']
#         self.amount = amount
#         self.aim = {'find_him': 'Найти и уничожить',
#                     'stolen_item': 'Вернуть украденную вешь владельцу',
#                     'foreign territory': 'Уничтожить отряд противника',
#                     'old_tech': 'Разведать обозначенную учёными местность'}
#         self.scenario_to_dif = {'find_him': False, 'stolen_item': False, 'foreign territory': True, 'caravan': False,
#                                 'old_tech': True}
#
#     async def add_missions(self):
#         with open('scenarios.json', encoding="utf8") as scenarios:
#             req = json.load(scenarios)
#             scenario = req['missions']
#             items = req['items']
#         for elem in self.town_letters:
#             for i in range(self.amount):
#                 scen = random.choice(list(scenario.keys()))
#                 diff = random.randint(1, 2)
#                 if scen != 'stolen_item':
#                     if self.scenario_to_dif[scen]:
#                         diff = 3
#                     self.missions.append(
#                         {'time': random.randint(1, 60), 'difficulty': diff, 'descript': random.choice(scenario[scen]),
#                          'aim': self.aim[scen]})
#                 else:
#                     line = random.choice(scenario[scen])
#                     line = line.replace('item', random.choice(items))
#                     self.missions.append(
#                         {'time': random.randint(1, 60), 'difficulty': diff, 'descript': line,
#                          'aim': self.aim[scen]})
#             await self.show_mission(elem)
#             self.missions = []
#
#     # async def show_mission(self, letter):
#     #     for guild in self.bot.guilds:
#     #         channel = get(guild.text_channels, name=f"📋доска-объявлений-{letter}")
#     #         if channel is not None:
#     #             for elem in self.missions:
#     #                 embed = nextcord.Embed(
#     #                     title=f"Доступен контракт",
#     #                     color=nextcord.Color.from_rgb(255, 160, 122)
#     #                 )
#     #
#     #                 embed.add_field(name="\u200b", value=f"```{elem['descript']}```", inline=False)
#     #                 embed.add_field(name="**Цель:**", value=f"**{elem['aim']}**", inline=True)
#     #                 embed.add_field(name="\u200b", value="\u200b", inline=True)
#     #                 embed.add_field(name="**Сложность:**", value=f"**{elem['difficulty']}**", inline=True)
#     #
#     #                 await channel.send(
#     #                     embed=embed,
#     #                     components=[Button(style=ButtonStyle.blue, label="Взять контракт")]
#     #                 )
#
#
# class BattleCreation:
#     def __init__(self, dif):
#         self.difficulty = dif
#         self.names = json.load(open("json_data/names.json", encoding="utf8"))
#         self.sir_names = json.load(open("json_data/nicknames.json", encoding="utf8"))
#
#     async def create_buddies(self):
#         name = f'{random.choice(self.names)} {random.choice(self.sir_names)}'
#         mag_cap = random.choice([5, 15, 30, 60])
#         fire_mods = ['semi']
#         if mag_cap == 15:
#             fire_mods.append('pew - pew')
#         if mag_cap >= 30:
#             fire_mods.append('auto')
#
#         if self.difficulty == 1:
#             return {
#                 'fight_stats': {
#                     'hp': random.randint(20, 40),
#                     'armor': random.randint(5, 15),
#                     'damage': random.randint(7, 15),
#                     'aim': random.randint(5, 14),
#                     'mag': mag_cap,
#                     'max_mag': mag_cap,
#                     'fire_mods': fire_mods,
#                     'cur_mod': random.choice(fire_mods)
#                 },
#                 'stats': {
#                     'race_bonus': 0,
#                     'streight': random.randint(5, 10),
#                     'intel': random.randint(5, 10),
#                     'motor': random.randint(5, 10),
#                     'speed': random.randint(5, 10), 'name': name
#                 }
#             }
#         elif self.difficulty == 2:
#             return {
#                 'fight_stats': {
#                     'hp': random.randint(30, 60),
#                     'armor': random.randint(10, 35),
#                     'damage': random.randint(14, 30),
#                     'aim': random.randint(10, 18),
#                     'mag': mag_cap,
#                     'max_mag': mag_cap,
#                     'fire_mods': fire_mods,
#                     'cur_mod': random.choice(fire_mods)
#                 },
#                 'stats': {
#                     'race_bonus': 0,
#                     'streight': random.randint(10, 17),
#                     'intel': random.randint(10, 17),
#                     'motor': random.randint(10, 17),
#                     'speed': random.randint(10, 17),
#                     'name': name
#                 }
#             }
#         elif self.difficulty == 3:
#             return {
#                 'fight_stats': {
#                     'hp': random.randint(40, 80),
#                     'armor': random.randint(25, 60),
#                     'damage': random.randint(20, 45),
#                     'aim': random.randint(20, 29),
#                     'mag': mag_cap,
#                     'max_mag': mag_cap,
#                     'fire_mods': fire_mods,
#                     'cur_mod': random.choice(fire_mods)
#                 },
#                 'stats': {
#                     'race_bonus': 0,
#                     'streight': random.randint(20, 30),
#                     'intel': random.randint(20, 34),
#                     'motor': random.randint(30, 50),
#                     'speed': random.randint(30, 40),
#                     'name': name
#                 }
#             }
#
#     async def start_battle(self, guild, member):
#         dil = {
#             'fight_stats': {
#                 'hp': 40000,
#                 'armor': 15,
#                 'damage': 7,
#                 'aim': 7,
#                 'mag': 10,
#                 'max_mag': 15,
#                 'fire_mods': ['semi', 'pew - pew', 'auto'],
#                 'cur_mod': 'semi'
#             },
#             'stats': {
#                 'race_bonus': 15,
#                 'streight': 10,
#                 'intel': 9,
#                 'motor': 20,
#                 'speed': 7,
#                 'name': 'tester'
#             }
#         }
#
#         enemy = []
#         dif_to_count = {1: (1, 5), 2: (2, 4), 3: (1, 3)}
#         diap = dif_to_count[self.difficulty]
#         for i in range(random.randint(diap[0], diap[1])):
#             enemy.append(Person(await self.create_buddies()))
#
#         channel_name = f"комната-{''.join(filter(str.isalnum, member.name))}".lower()
#         channel = get(guild.channels, name=channel_name)
#         if channel:
#             await channel.delete()
#         category = get(guild.categories, name="Битвы")
#         channel = await guild.create_text_channel(channel_name, category=category)
#
#         await channel.set_permissions(guild.default_role, send_messages=False, read_messages=False)
#         await channel.set_permissions(member, send_messages=True, read_messages=True)
#         start = Battle(channel, self.difficulty, member.id)
#         await start.add_persons([[Person(dil)], enemy])
#         BATTLES_ID[member.id] = start
#
#
# class Battle:
#     def __init__(self, channel, diff, mem, bot):
#         self.warriors = {'player': [], 'enemy': []}
#         self.queue = 'Player'
#         self.channel = channel
#         self.enemy_counter = 0
#         self.difficulty = diff
#         self.member = mem
#         self.od = 5
#         self.message = None
#         self.turn_message = None
#         self.enemy_message = None
#         self.bot = bot
#
#     async def add_persons(self, persons):
#         self.warriors['player'] = persons[0]
#         self.warriors['enemy'] = persons[1]
#         self.enemy_counter = len(persons[1])
#         await self.show_stats()
#
#     async def get_reward(self):
#         dif_to_rew = {1: 100, 2: 500, 3: 1000}
#         total_reward = dif_to_rew[self.difficulty] * self.enemy_counter
#         await self.channel.send(
#             f'За выполнение задания вы получили {total_reward} '
#             f'{self.bot.get_emoji(EMOJIS_ID["Валюта"])}'
#         )
#         users = DB_SESSION.query(User).all()
#         for elem in users:
#             if elem.id == f'{self.member}-{self.message.guild.id}':
#                 elem.balance += total_reward
#                 break
#         DB_SESSION.commit()
#
#     async def win_lose(self, win):
#         await self.channel.send('**__Итоги битвы__**')
#         if win:
#             await self.channel.send('**Победа**')
#             await self.get_reward()
#         else:
#             await self.channel.send('**Поражение**')
#         await self.channel.send('Этот чат удалиться через 1 минуту')
#         await asyncio.sleep(60)
#         await self.channel.delete()
#
#     async def get_od(self):
#         return self.od
#
#     async def show_stats(self):
#         if self.od > 0:
#             player = self.warriors['player'][0]
#             if self.turn_message is None:
#                 self.turn_message = await self.channel.send('**___Ваш ход___**')
#             fight_stats = await player.get_fight_stats()
#             hp = fight_stats['hp']
#             armor = fight_stats['armor']
#             bonuses = await player.add_get_clear_bonus('get')
#             if 'armor+' in bonuses:
#                 armor += bonuses['armor+']
#             embed = nextcord.Embed(title=f"Ваши Показатели", color=nextcord.Color.from_rgb(255, 255, 255))
#             embed.add_field(name="**Ваше ОЗ**", value=hp, inline=True)
#             embed.add_field(name="**Ваша Защита**", value=armor, inline=True)
#             components = [
#                 Button(style=ButtonStyle.red, label="Атаковать"),
#                 Button(style=ButtonStyle.blue, label="Укрыться"),
#                 Button(style=ButtonStyle.green, label="Лечиться"),
#                 Button(style=ButtonStyle.gray, label="Перезарядиться"),
#                 Button(style=ButtonStyle.gray, label="Сменить режим стрельбы")
#             ]
#             if self.message is None:
#                 self.message = await self.channel.send(
#                     embed=embed,
#                     components=[components]
#                 )
#             else:
#                 await self.message.edit(embed=embed)
#
#     async def player_turn(self, action):
#         if self.od > 0:
#             player = self.warriors['player'][0]
#             player_fight_stats = await player.get_fight_stats()
#             player_stats = await player.get_stats()
#             if action == 1:
#                 embed = nextcord.Embed(
#                     title=f"Список противников",
#                     color=nextcord.Color.from_rgb(255, 0, 0)
#                 )
#                 components = []
#                 for elem in self.warriors['enemy']:
#                     raw_info = await elem.get_info()
#                     name = raw_info[0]
#                     info = raw_info[1]
#                     embed.add_field(name=f"**{self.warriors['enemy'].index(elem) + 1}) {name}**",
#                                     value=f'ОЗ: {info[0]}, Защита: {info[1]}',
#                                     inline=True)
#                     components.append(Button(style=ButtonStyle.gray, label=f"{self.warriors['enemy'].index(elem) + 1}"))
#                 self.enemy_message = await self.channel.send(embed=embed, components=[components])
#
#             elif action == 2:
#                 a = await self.hide(player)
#                 if a >= 0:
#                     self.od -= 1
#                     await self.show_stats()
#                     return f'Вы спрятались, ваша защита стала {a} единиц'
#                 else:
#                     self.od -= 1
#                     await self.show_stats()
#                     return 'Вы не смогли спрятаться'
#
#             elif action == 3:
#                 if player_fight_stats['mag'] == player_fight_stats['max_mag']:
#                     await self.show_stats()
#                     return 'Перезарядка не требуется'
#                 else:
#                     base_motor = 25 + player_stats['motor']
#                     a = random.randint(1, 100)
#                     if a <= base_motor:
#                         await player.reload()
#                         self.od -= 1
#                         await self.show_stats()
#                         return 'Вы успешно перезарядили оружие'
#                     else:
#                         self.od -= 1
#                         await self.show_stats()
#                         return 'Вы не смогли перезарядить оружие'
#
#             elif action == 4:
#                 heal = 15 + random.randint(1, player_stats['intel'] // 2)
#                 await player.heal(heal)
#                 self.od -= 1
#                 await self.show_stats()
#                 return f'Вы восполнили своё здоровье на {heal} hp'
#             elif action == 5:
#                 return await player.change_mode()
#
#     async def choice_enemy(self, action):
#         player = self.warriors['player'][0]
#         enemy = self.warriors['enemy'][action - 1]
#         enemy_name, enemy_data = await enemy.get_info()
#         a = await self.attack(enemy, player)
#         text_to_return = ''
#         if type(a) != str:
#             if a > 0:
#                 text_to_return = f'Вы нанесли урон {enemy_name} в размере {a} hp'
#                 chosen_enemy_stats = await self.warriors['enemy'][action - 1].get_fight_stats()
#                 if chosen_enemy_stats['hp'] <= 0:
#                     self.warriors['enemy'].remove(self.warriors['enemy'][action - 1])
#                     if len(self.warriors['enemy']) == 0:
#                         await self.win_lose(True)
#             else:
#                 text_to_return = f'Вы не смогли нанести противнику {enemy_name} урон'
#         elif type(a) == str:
#             text_to_return = a
#         self.od -= 1
#         await self.show_stats()
#         await self.enemy_message.delete()
#         return text_to_return
#
#     async def enemy_turn(self):
#         more = True
#         player = self.warriors['player'][0]
#         player_stats = await player.get_fight_stats()
#         await self.channel.send('**___Ход противника___**')
#         for elem in self.warriors['enemy']:
#             person = await elem.get_stats()
#             await self.channel.send(f'**{person["name"]}**')
#             od = 5
#             warrior = elem
#             warrior_basic_stats = await warrior.get_stats()
#             heal_point, hide_point, armor_point, min_mag = await warrior.get_static_fight_stats()
#
#             while od >= 1:
#                 warrior_stats = await warrior.get_fight_stats()
#                 if (warrior_stats['hp'] < hide_point and warrior_stats['armor'] >= armor_point) or \
#                         warrior_stats['hp'] < heal_point:
#                     heal = 4 + random.randint(1, warrior_basic_stats['intel'] // 2)
#                     await self.channel.send(f'Противник восполнил своё здоровье на {heal} hp')
#                     await warrior.heal(heal)
#                     od -= 1
#                 elif warrior_stats['hp'] < hide_point and warrior_stats['armor'] <= armor_point:
#                     a = await self.hide(warrior)
#                     if a >= 0:
#                         await self.channel.send(f'Противник спрятался, его защита возросла на {a} единиц')
#                     else:
#                         await self.channel.send('Противник не смог спрятаться')
#                     od -= 1
#                 elif warrior_stats['mag'] <= min_mag:
#                     if warrior_stats['mag'] != warrior_stats['max_mag']:
#                         base_motor = 15 + warrior_basic_stats['motor']
#                         a = random.randint(1, 100)
#                         if a <= base_motor:
#                             await warrior.reload()
#                             await self.channel.send('Противник успешно перезарядил оружие')
#                         else:
#                             await self.channel.send('Противник не смог перезарядить оружие')
#                         od -= 1
#                 else:
#                     dealed_damage = await self.attack(self.warriors['player'][0], warrior)
#                     if dealed_damage > 0:
#                         await self.channel.send(f'Вам нанесли урон в размере {dealed_damage} hp')
#                         if player_stats['hp'] <= 0:
#                             await self.win_lose(False)
#                             more = False
#                             break
#                     od -= 1
#
#             if not more:
#                 break
#         if more:
#             self.od = 5
#             self.turn_message = None
#             self.message = None
#             await self.show_stats()
#
#     @staticmethod
#     async def hide(warrior):
#         warrior_stats = await warrior.get_stats()
#         warrior_fight_stats = await warrior.get_fight_stats()
#         base_speed = 15 + warrior_stats['speed']
#         arm_bonus = {'field': 0, 'tree': 15, 'rock': 20, 'baricade': 30}
#         a = random.randint(1, 100)
#         if a <= base_speed:
#             hide = random.choice(('field', 'tree', 'rock', 'baricade'))
#             await warrior.add_get_clear_bonus('add', 'armor+', arm_bonus[hide])
#             return arm_bonus[hide] + warrior_fight_stats['armor']
#         else:
#             return 0
#
#     @staticmethod
#     async def attack(target, warrior):
#         base_aim = 30
#         fight_stats = await warrior.get_fight_stats()
#         fire_mode = fight_stats['cur_mod']
#         mag = fight_stats['mag']
#         play_damage = fight_stats['damage']
#         play_aim = fight_stats['aim']
#         en_armor = fight_stats['armor']
#         total_damage = 0
#         if 'armor+' in await target.add_get_clear_bonus('get'):
#             bonuses = await target.add_get_clear_bonus('get')
#             en_armor += bonuses['armor+']
#         if 'aim+' in await warrior.add_get_clear_bonus('get'):
#             bonuses = await warrior.add_get_clear_bonus('get')
#             base_aim += bonuses['aim+']
#         if fire_mode == 'semi' and mag >= 1:
#             shoots = 1
#             await warrior.shoot(1)
#         elif fire_mode == 'pew - pew' and mag >= 3:
#             await warrior.shoot(3)
#             shoots = 3
#             base_aim -= 20
#         elif fire_mode == 'auto' and mag >= 10:
#             await warrior.shoot(10)
#             shoots = 10
#             base_aim -= 25
#         else:
#             return 'Недостаточно патронов'
#
#         for i in range(shoots):
#             if random.randint(1, 100) <= base_aim + play_aim and play_damage > en_armor * 0.01:
#                 await target.get_hurt(play_damage - en_armor * 0.01)
#                 await warrior.add_get_clear_bonus('clear', 'aim+')
#                 total_damage += play_damage - en_armor * 0.01
#             else:
#                 await warrior.add_get_clear_bonus('add', 'aim+', 10)
#
#         return total_damage
#
#
# class ServerSetupCog(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#
#     @nextcord.slash_command(
#         name="mission_run",
#         description="Генерирует миссии на досках объявлений.",
#         guild_ids=TEST_GUILDS_ID
#     )
#     async def mission_run(
#             self,
#             interaction: Interaction,
#     ):
#         a = TownMissions(random.randint(1, 7))
#         await a.add_missions()
#
#
# def setup(bot):
#     bot.add_cog(ServerSetupCog(bot))
