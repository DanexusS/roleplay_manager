import sqlalchemy
from .db_session import SqlAlchemyBase


# Таблца игроков
class Items(SqlAlchemyBase):
    __tablename__ = 'items'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    name = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    type = sqlalchemy.Column(sqlalchemy.String)
    damage = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    aim = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    ammunition = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    hp_regen = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    protection = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    price = sqlalchemy.Column(sqlalchemy.Integer)
