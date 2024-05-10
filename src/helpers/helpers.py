import yaml

CONFIG_FILE_PATH = "config/config.yaml"
SECRETS_FILE_PATH = "config/.secrets.yaml"


def get_config(path_to_config: str = CONFIG_FILE_PATH):
    """
    :param path_to_config: optional path of config file to load
    """
    config = {}
    with open(path_to_config, "r") as stream:
        config = yaml.safe_load(stream)

    return config


def get_secrets(path_to_secrets: str = SECRETS_FILE_PATH):
    """
    :param path_to_secrest: optional path of secrets file to load
    """
    config = {}
    with open(path_to_secrets, "r") as stream:
        config = yaml.safe_load(stream)

    return config


if __name__ == "__main__":
    pass
