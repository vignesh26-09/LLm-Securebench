from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
class Base(DeclarativeBase): pass
def make_engine(url:str):
 if url == "sqlite:///:memory:": return create_engine(url, future=True, connect_args={"check_same_thread":False}, poolclass=StaticPool)
 return create_engine(url, future=True)
def make_session_factory(url:str): return sessionmaker(make_engine(url), expire_on_commit=False, class_=Session)
def create_schema(url:str):
 engine=make_engine(url); Base.metadata.create_all(engine); return engine
