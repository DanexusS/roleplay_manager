import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    nation = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    origin = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    money = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    health = sqlalchemy.Column(sqlalchemy.Integer)
    strength = sqlalchemy.Column(sqlalchemy.Integer)
    intelligence = sqlalchemy.Column(sqlalchemy.Integer)
    dexterity = sqlalchemy.Column(sqlalchemy.Integer)
    speed = sqlalchemy.Column(sqlalchemy.Integer)

    inventory = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    news = orm.relation("News", back_populates='user')
