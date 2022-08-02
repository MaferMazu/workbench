"""This encapsulates some boilerplate workbench client code."""

import configparser
import argparse
import os

def grab_server_args():
    """Grab server info from configuration file"""
    
    workbench_conf = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
    workbench_conf.read(config_path)
    server = workbench_conf.get('workbench', 'server_uri')
    port = workbench_conf.get('workbench', 'server_port')

    # Collect args from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', type=str, default=server, help='location of workbench server')
    parser.add_argument('-p', '--port', type=int, default=port, help='port used by workbench server')
    args, commands = parser.parse_known_args()
    server = str(args.server)
    port = str(args.port)

    return {'server':server, 'port':port, 'commands': commands}
