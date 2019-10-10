#!/usr/bin/env python3

from marathon_deploy.utils.common import parse_arguments, create_client
import sys
import time

# Hide urllib warnings for insecure certificates
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import warnings
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


def main():
    args = parse_arguments()

    if args.appid is None:
        print("appid must be defined")
        sys.exit(1)

    client = create_client(args.marathon, args.user, args.password, args.https_verify)

    time.sleep(20)
    check = True

    while check:
        my_app = client.get_app(args.appid)
        if my_app.tasks_running >= 1 and my_app.tasks_healthy >= 1:
            check = False
            print("APP deploy on Marathon")
        else:
            if my_app.tasks_staged >= 1:
                print("APP in staging mode")

        time.sleep(1)


if __name__ == '__main__':
    main()
