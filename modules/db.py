import logging
from sqlalchemy import Column, Integer, String,Text, Boolean, DateTime, func
from sqlalchemy import create_engine, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from modules.rtsp import Target

Base = declarative_base()


class Result(Base):
    __tablename__ = 'rtsp_bruter_result'

    id = Column(Integer, primary_key=True)
    brute_id = Column(String(255))
    created_at = Column(DateTime, default=func.now(), nullable=False)

    ip_address = Column(String(255))
    port = Column(Integer)
    is_connect = Column(Boolean)

    is_route = Column(Boolean)
    route = Column(String(255))
    route_trial = Column(Integer, default=0)

    is_creds = Column(Boolean)
    creds = Column(String(255))
    creds_trial = Column(Integer, default=0)

    is_screen = Column(Boolean)
    is_final = Column(Boolean)

    status = Column(String(30))
    auth_method = Column(String(30))
    last_error = Column(Text(2000))
    cseq = Column(Integer)
    data = Column(Text(length=4294967295))
    screen = Column(Text(length=4294967295))

    _table_args__ = (
        UniqueConstraint(brute_id, ip_address, port, name='brute_id_ip_port__idx'),
        Index('brute_id__idx', 'brute_id')
    )

    def get_state(self):
        state = {}
        for key in ['id', 'ip_address', 'port', 'is_connect',
                    'is_route', 'route', 'is_creds', 'creds', 'is_screen',
                    'is_final', 'status', 'auth_method', 'last_error', 'cseq', 'screen']:
            state[key] = getattr(self, key)
        return state

    def set(self, field: str, value):
        setattr(self, field, value)

    def set_target_common_values(self, target: Target):
        self.set('brute_id', str(target.brute_id))
        self.set('status', str(target.status.value))
        self.set('last_error', str(target.last_error))
        self.set('data', str(target.data))
        self.set('auth_method', str(target.auth_method.value))
        self.set('cseq', target.cseq)


def init_db(url, debug):
    engine = create_engine(url, echo=False,  pool_size=50, pool_timeout=60)
    logging.getLogger('sqlalchemy').setLevel(logging.INFO if debug else logging.ERROR)
    session = sessionmaker(bind=engine)

    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    return engine, session
