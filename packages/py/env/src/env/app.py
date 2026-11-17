"""Application identity shared by app-local libraries and generated modules."""

from env._base import BaseEnv


class Env(BaseEnv):
    app_name: str = "app-workspace"
    apaleo_connector: str = "apaleo_b9e2"


env = Env()
