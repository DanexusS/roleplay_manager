import sqlalchemy
from .db_session import SqlAlchemyBase


# Таблца игроков
class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    name = sqlalchemy.Column(sqlalchemy.String, default="-1")
    nation = sqlalchemy.Column(sqlalchemy.String, default="-1")
    origin = sqlalchemy.Column(sqlalchemy.String, default="-1")

    balance = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    level = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    xp = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    skill_points = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    health = sqlalchemy.Column(sqlalchemy.Integer, default=5)
    strength = sqlalchemy.Column(sqlalchemy.Integer, default=5)
    intelligence = sqlalchemy.Column(sqlalchemy.Integer, default=5)
    dexterity = sqlalchemy.Column(sqlalchemy.Integer, default=5)
    speed = sqlalchemy.Column(sqlalchemy.Integer, default=5)

    inventory = sqlalchemy.Column(sqlalchemy.String, default="")
    equipped_inventory = sqlalchemy.Column(sqlalchemy.String, default="")
