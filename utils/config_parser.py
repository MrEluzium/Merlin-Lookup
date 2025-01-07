import configparser


def create_config(filename: str) -> None:
    config = configparser.ConfigParser()

    config['Bot'] = {'BOT_TOKEN': '<BOT TOKEN>',
                     'PAYMENT_TOKEN': '<PAYMENT TOKEN>',
                     'ADMIN_USERS': []}
    config['Database'] = {'DB_NAME': '<DATABASE NAME>',
                          'DB_USER': 'postgres',
                          'DB_PASSWORD': '<PASSWORD>',
                          'DB_HOST': '172.17.0.1',
                          'DB_PORT': '5432'}
    config['Library'] = {'LIBRARY_ROOT': '<LIBRARY ROOT>', }

    with open(filename, 'w') as configfile:
        config.write(configfile)


def read_config(filename: str) -> dict:
    config = configparser.ConfigParser()
    config.read(filename)
    return config._sections


def write_config(filename: str, sections: dict) -> None:
    config = configparser.ConfigParser()

    for section, settings in sections.items():
        if section not in config:
            config.add_section(section)
        for key, value in settings.items():
            config[section][key] = str(value)

    with open(filename, 'w') as configfile:
        config.write(configfile)
