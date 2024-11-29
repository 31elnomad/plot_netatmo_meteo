import argparse

def main(arg):
    print(f"Argument reçu : {arg}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-cfg", help="cfg", required=True)
    args = parser.parse_args()
    main(args.cfg)
