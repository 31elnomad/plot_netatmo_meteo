import argparse
import configparser
import sys
sys.path.append('scripts')
from getdata_api import token

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-cfg", help="cfg", required=True)
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config.read(args.cfg)

    data_obj = token(config)
    data_obj.getdata()
