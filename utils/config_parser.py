import configparser


def create_config(filename: str) -> None:
    config = configparser.ConfigParser()

    config['Bot'] = {'BOT_TOKEN': '<BOT TOKEN>',
                     'PAYMENT_TOKEN': '<PAYMENT TOKEN>'}
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
