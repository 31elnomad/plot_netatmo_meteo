import argparse
import configparser

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-cfg", help="cfg", required=True)
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config.read(args.cfg)
    print(config)
