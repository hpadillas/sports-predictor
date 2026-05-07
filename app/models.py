from sqlalchemy import Table, Column, Integer, String, MetaData, TIMESTAMP

metadata = MetaData()

matches = Table(
    "matches",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("league", String),
    Column("home_team", String),
    Column("away_team", String),
    Column("home_goals", Integer),
    Column("away_goals", Integer),
    Column("date", TIMESTAMP),
)