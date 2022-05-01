import sqlalchemy
from .db_session import SqlAlchemyBase


# Таблца игроков
class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    name = sqlalchemy.Column(sqlalchemy.String)
    nation = sqlalchemy.Column(sqlalchemy.String)
    origin = sqlalchemy.Column(sqlalchemy.String)

    balance = sqlalchemy.Column(sqlalchemy.Integer)

    level = sqlalchemy.Column(sqlalchemy.Integer)
    xp = sqlalchemy.Column(sqlalchemy.Integer)
    skill_points = sqlalchemy.Column(sqlalchemy.Integer)

    health = sqlalchemy.Column(sqlalchemy.Integer)
    strength = sqlalchemy.Column(sqlalchemy.Integer)
    intelligence = sqlalchemy.Column(sqlalchemy.Integer)
    dexterity = sqlalchemy.Column(sqlalchemy.Integer)
    speed = sqlalchemy.Column(sqlalchemy.Integer)

    inventory = sqlalchemy.Column(sqlalchemy.String)
