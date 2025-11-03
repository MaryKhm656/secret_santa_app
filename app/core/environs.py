from environs import Env

env = Env()
env.read_env()


DATABASE_URL = env("DATABASE_URL")
SECRET_KEY = env("SECRET_KEY")
