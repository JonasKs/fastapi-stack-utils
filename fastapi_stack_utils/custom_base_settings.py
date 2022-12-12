import contextlib
from typing import Literal

from pydantic import BaseSettings, Field, HttpUrl
from pydantic.env_settings import SettingsSourceCallable
from pydantic_vault import vault_config_settings_source


class SettingsConfig(BaseSettings.Config):
    env_file = '.env.override'
    env_file_encoding = 'utf-8'
    vault_url: HttpUrl = HttpUrl('https://vault.intility.com', scheme='https')

    with contextlib.suppress(ModuleNotFoundError):
        from azure.identity import ClientSecretCredential
        from azure.identity.aio import ClientSecretCredential as AsyncClientSecretCredential

        keep_untouched = (AsyncClientSecretCredential, ClientSecretCredential)


class Env(BaseSettings):
    ENVIRONMENT: Literal['dev', 'lab', 'prod', 'qa', 'test'] = Field('dev', env='ENVIRONMENT')

    class Config(SettingsConfig):
        """
        Just inherit the shared settings, no overrides
        """

        pass


env = Env()


class CustomBaseSettings(BaseSettings):
    ENVIRONMENT = env.ENVIRONMENT

    class Config(SettingsConfig):
        """
        Inherit the shared settings and override the custom source to add vault if in dev
        """

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            """
            Adds inn vault as pydantic config source if in dev
            """
            if env.ENVIRONMENT == 'dev':
                return init_settings, env_settings, vault_config_settings_source, file_secret_settings
            else:
                return init_settings, env_settings, file_secret_settings
