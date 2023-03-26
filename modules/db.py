from sqlalchemy import create_engine, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Result(Base):
    __tablename__ = 'result'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String)
    port = Column(Integer)
    is_connect = Column(Boolean)
    is_route = Column(Boolean)
    is_creds = Column(Boolean)
    is_screen = Column(Boolean)

    creds_user = Column(String)
    creds_pass = Column(String)

    _table_args__ = (
        UniqueConstraint(ip_address, port, name='ip_port__idx')  # add an index on the 'name' column
    )

def init_db(keep: bool):
    engine = create_engine('sqlite:///bruter.db')
    session = sessionmaker(bind=engine)


    if not keep:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    return engine, session
