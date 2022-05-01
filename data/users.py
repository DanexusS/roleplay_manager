import sqlalchemy
from .db_session import SqlAlchemyBase


# Таблца игроков
class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    nation = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    origin = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    balance = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    level = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    xp = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    skill_points = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    health = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    strength = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    intelligence = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    dexterity = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    speed = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    inventory = sqlalchemy.Column(sqlalchemy.String, nullable=True)
