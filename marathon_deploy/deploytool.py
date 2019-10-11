#!/usr/bin/env python3

import sys
import os
import marathon_deploy.utils.actions as actions
from marathon_deploy.utils.common import parse_arguments, check_appid,\
    create_client

# Hide urllib warnings for insecure certificates
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import warnings
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


def main():  # pylint: disable=too-many-branches
    args = parse_arguments()

    if args.appid:
        if args.appid.startswith('/'):
            args.appid = args.appid
        else:
            args.appid = '/' + args.appid

    client = create_client(args.marathon, args.user, args.password, args.https_verify)

    if args.version:
        version_filepath = os.path.join(os.path.dirname(__file__),
                                        'marathon_deploy', 'version.txt')
        with open(version_filepath) as version_file:
            print(version_file.read())
        sys.exit(0)

    elif args.put:
        actions.put_app(client, args.put, args.fullrollback)

    elif args.tag and check_appid(args.appid):
        actions.update_app_tag(client, args.appid, args.tag)

    elif args.restart and check_appid(args.appid):
        actions.rolling_restart_app(client, args.appid)

    elif args.inplacerestart and check_appid(args.appid):
        actions.in_place_restart(client, args.appid)

    elif check_appid(args.appid) and args.scale is not None:
        actions.scale_application(client, args.appid, args.scale)

    elif args.instances and check_appid(args.appid):
        print(actions.get_instances_amount(client, args.appid))

    elif args.saveapp and check_appid(args.appid):
        actions.save_application(client, args.appid)

    elif args.dumpall:
        actions.dump_all_apps(client)

    else:
        print("Nothing done")


if __name__ == '__main__':
    main()
