import yaml


class Localization:
    def __init__(self, file_path):
        """
        Initialize the Localization object and load the YAML file into memory.
        :param file_path: Path to the YAML localization file.
        """
        self.messages = {}
        self.load_file(file_path)

    def load_file(self, file_path):
        """
        Load the YAML file into memory.
        :param file_path: Path to the YAML localization file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.messages = yaml.safe_load(file)
        except FileNotFoundError:
            raise Exception(f"Localization file '{file_path}' not found.")
        except yaml.YAMLError as e:
            raise Exception(f"Error parsing YAML file: {e}")

    def get(self, *keys) -> str:
        """
        Retrieve a localized message by a series of nested keys.
        :param keys: Keys representing the path to the desired message.
        :return: Localized message string.
        """
        try:
            message = self.messages
            for key in keys:
                message = message[key]
            return message
        except KeyError:
            raise Exception(f"Message path {' -> '.join(keys)} not found in localization file.")


l18n = Localization("l18n.yaml")
