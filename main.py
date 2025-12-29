import getopt
import sys

from dotenv import load_dotenv

from weather.notify import run_notifier


def main():
    arguments = sys.argv[1:]
    short_options = "w"
    long_options = "weather"
    try:
        args, _ = getopt.getopt(arguments, short_options, long_options)
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    for arg, _ in args:
        if arg in ("-w", "--weather"):
            res = load_dotenv("weather/.env")
            print(res)
            run_notifier()


if __name__ == "__main__":
    main()
