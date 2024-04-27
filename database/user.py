'''
File includes the schemas for telegram_users table
as well as all the direct querying logic for the full app through UserRepository Class
'''

from sqlalchemy import Column, String,DateTime, func

from sqlalchemy.orm import relationship

from .base import Base, Session
from .configurations import Configurations

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import Base
from marzban_api.marzban_api_facade import MarzbanApiFacade
from logger import logger

class User(Base):
    __tablename__ = 'telegram_users'

    telegram_user_id = Column(String(255), primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    configurations = relationship('Configurations', back_populates='user')

    def __init__(self, telegram_user_id):
        self.telegram_user_id = telegram_user_id

class UserRepository(): 
    @staticmethod
    def get_user(telegram_user_id): 
        with Session() as session: 
            with session.begin(): 
                try: 
                    logger.info('get_user -> grabbing user\'s data')
                    user = session.query(User).filter_by(telegram_user_id=telegram_user_id).first()
                    configurations = None if user == None else user.configurations
                    session.close()
                except Exception:
                    logger.error(f"Exception -> get_user: ", exc_info=True)
                    session.rollback()

        return [user, configurations]
    
    @staticmethod
    def get_user_configurations(telegram_user_id): 
        with Session() as session: 
            with session.begin(): 
                try: 
                    logger.info('get_user_configurations -> grabbing users configs')
                    configurations = session.query(Configurations).filter_by(telegram_user_id=telegram_user_id).all()
                except Exception:
                    logger.error(f"Exception -> get_user_configurations: ", exc_info=True)
                    session.rollback()
        return configurations


    @staticmethod
    def create_new_user(telegram_user_id): 
        with Session() as session: 
            with session.begin(): 
                try: 
                    logger.info('create_new_user -> creating new user')
                    new_user = User(telegram_user_id)
                    session.add(new_user)
                except Exception:
                    logger.error(f"Exception -> create_new_user: ", exc_info=True)
                    session.rollback()
                finally:
                    session.commit()
        
    @staticmethod
    def insert_configurations(telegram_user_id, links): 
        with Session() as session: 
            with session.begin(): 
                try: 
                    logger.info('insert_configurations -> inserting user configs')
                    configs = [Configurations(telegram_user_id, link) for link in links]
                    session.bulk_save_objects(configs)
                except Exception:
                    logger.error(f"Exception -> insert_configurations: ", exc_info=True)
                    session.rollback()
                finally:
                    session.commit()
    

    @staticmethod
    def refresh_configs(access_token): 
        session = Session()
        users = session.query(User).all()
        for user in users: 
            user_marzban_data, _ = MarzbanApiFacade.get_user(user.telegram_user_id, access_token)
            new_configs = [Configurations(user.telegram_user_id, link) for link in user_marzban_data['links']]
            try:
                existing_configs = session.query(Configurations).filter_by(telegram_user_id=user.telegram_user_id).all()
                for config in existing_configs:
                    session.delete(config)
                session.bulk_save_objects(new_configs)
                session.commit()
            except Exception:
                logger.error(f"Exception -> refresh_configs: ", exc_info=True)
                session.rollback()
            finally:
                session.close()

