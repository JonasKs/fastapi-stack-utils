from fastapi_stack_utils.cli.load_docker_env import load_docker_env
from typer import Typer

cli = Typer()


@cli.command()
def load_env() -> None:
    """
    Loads environment variables for Docker from Vault and writes to `.env`.
    Warning: Will overwrite `.env` file.
    Requires `vault` to be installed
    """
    load_docker_env()


@cli.command()
def filler() -> None:
    """
    A filler command to enable the `fsu` command to have subcommands.
    Allowing addition of new commands in future
    """
    print('Filler Command')  # noqa: T001
