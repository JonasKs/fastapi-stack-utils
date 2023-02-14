import os
import subprocess
from subprocess import CalledProcessError


def load_docker_env() -> None:
    """
    Reads secrets from Vault for project and writes docker specific environment variables to `.env`
    Checks if user has valid token, if not, triggers loging flow for Vault CLI
    Uses repo name from git as path for Vault
    """
    git_remote = subprocess.run(['git', 'remote', '-v'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

    project_name = (
        git_remote.split('\n')[0]
        .split()[1]
        .split('@')[1]
        .split(':')[1]
        .split('/')[-1]
        .removesuffix('.git')
        .strip()
        .removesuffix('-backend')
        .removesuffix('-build')
    )

    vault_address = os.environ.get('VAULT_ADDR', 'https://vault.intility.com')

    try:
        subprocess.run(
            ['vault', 'token', 'lookup', f'-address={vault_address}'], check=True, stdout=subprocess.PIPE
        ).stdout.decode('utf-8')
    except CalledProcessError:
        subprocess.run(
            ['vault', 'login', f'-address={vault_address}', '-method=oidc', '-path=aa'],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout.decode('utf-8')

    secrets = (
        subprocess.run(
            [
                'vault',
                'read',
                f'-address={vault_address}',
                '-field=data',
                '-format=yaml',
                f'kv-nsa/data/{project_name}/dev/',
            ],
            check=True,
            stdout=subprocess.PIPE,
        )
        .stdout.decode('utf-8')
        .replace(': ', '=')
    )

    docker_secrets = '\n'.join(
        [secret for secret in secrets.split('\n') if secret.split('=')[0] in ['POSTGRES_PASSWORD', 'REDIS_PASSWORD']]
    )

    with open('.env', 'w') as docker_env:
        docker_env.write(docker_secrets + '\n')
