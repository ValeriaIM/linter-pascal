import argparse
import logging
import configparser

__version__ = '1.1'
__author__ = 'ValeriaIM'
__email__ = 'vkvaleria2000@gmail.com'

import os

from linter import Linter
from setting import Setting

LOGGER_NAME = '3d-editor'
LOGGER = logging.getLogger(LOGGER_NAME)


def main():
    """Точка входа в приложение"""
    args = parse_args()
    linter = Linter()
    set_rules(args.config, linter)
    check_files(args.dir, linter)


def parse_args():
    """Разбор аргуметов запуска"""
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS]',
        description='Pascal linter. console version {}'.format(__version__),
        epilog='Author: {} <{}>'.format(__author__, __email__))

    parser.add_argument(
        '-c', '--config', type=str,
        metavar='FILENAME', default='settings.ini', help='configuration file')
    parser.add_argument(
        '-d', '--dir', type=str,
        metavar='DIRECTORY', default=r'Tests', help='directory with test files')
    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        '-l', '--log', type=str,
        metavar='FILENAME', default='linter.log', help='log filename')
    arg_group.add_argument(
        '--no-log',
        action='store_true', help='no log')

    return parser.parse_args()


def set_rules(file_name, linter):
    config = configparser.ConfigParser()
    config.read(file_name)
    setting_args = []

    if 'NAMES' in config:
        rules = config['NAMES']
        for key, value in rules.items():
            setting_args.append(value)
    else:
        setting_args.append([0 for i in range(5)])

    if 'INDENT' in config:
        rules = config['INDENT']
        for key, value in rules.items():
            setting_args.append(value)
    else:
        setting_args.append([0 for i in range(6)])

    if 'LINES' in config:
        rules = config['LINES']
        for key, value in rules.items():
            setting_args.append(value)
    else:
        setting_args.append([0 for i in range(2)])

    linter.set_setting(Setting(setting_args))


def check_files(dir_name, linter):
    files = os.listdir(dir_name)

    for file in files:
        s = 'Tests\\' + file
        print('\n' + file + ':')
        f = open(s)
        linter.process_code(f)


if __name__ == '__main__':
    main()

