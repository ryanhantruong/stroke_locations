'''Interact with google maps api'''
import os
import configparser


def get_key(config_path='config'):
    """
    Get the Google API keys from an external config file
    It looks like this:

    [api]
    api_number=<your api number>

    """
    config = configparser.ConfigParser()
    config.read(os.path.join(config_path, 'google_maps.cfg'))
    key = config['api']['api_number']
    return key
