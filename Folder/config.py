import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///d:\\DATA\\TEMORA2020_Test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_BINDS = {'db1': 'sqlite:///d:\\DATA\\TEMORA_KTRAX_01.db'}
    SECRET_KEY = 'asecret'
    SQLALCHEMY_TRACK_NOTIFICATIONS = False
