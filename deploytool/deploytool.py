#!/usr/bin/env python3

import argparse
import sys

from marathon import MarathonClient
from marathon.exceptions import MarathonError
import actions

__version__ = '2.0'

global timeout
timeout = 5


def main():

    args = parse_arguments()
    if args.timeout is not None:
        global timeout
        timeout = args.timeout
    

    if args.appid is not None:
        args.appid = args.appid if args.appid.startswith('/') else '/' + args.appid

    c = create_client(args.marathon)

    if args.version is not None:
        print(__version__)
        sys.exit(0)

    elif args.put is not None:
        actions.put_app(c, args.put, args.fullrollback)

    elif args.tag is not None and check_appid(args.appid):
        actions.update_app_tag(c, args.appid, args.tag)

    elif args.restart and check_appid(args.appid):
        actions.rolling_restart_app(c, args.appid, timeout)

    elif args.inplacerestart and check_appid(args.appid):
        actions.in_place_restart(c, args.appid, timeout)

    elif args.scale is not None and check_appid(args.appid):
        actions.scale_application(c, args.appid, args.scale, timeout)

    elif args.instances and check_appid(args.appid):
        print(actions.get_instances_amount(c, args.appid))

    elif args.list:
        print('Current applications:')
        [print('- {} -> {}'.format(a[0], a[1])) for a in actions.list_applications(c)]

    elif args.saveapp and check_appid(args.appid):
        actions.save_application(c, args.appid)

    elif args.dumpall:
        actions.dump_all_apps(c)

    else:
        print("Nothing done")


def check_appid(appid) -> bool:
    if appid is None:
        print("Error! --appid is required for the requested operation.")
        sys.exit(1)
    else:
        return True


def create_client(urls: str):
    marathonlist = urls.split(',')
    client = MarathonClient(marathonlist)
    try:
        if client.ping().strip() != b'pong':
            raise MarathonError
    except MarathonError:
        print('Could not connect to Marathon in {}'.format(marathonlist))
        sys.exit(1)
    return client


def parse_arguments():
    args = argparse.ArgumentParser()
    args.add_argument('--marathon', '-m', default='http://localhost:8080', help='Marathon where to run the application.'
                                                                                'Allows several URLs, comma separated.')
    args.add_argument('--appid', type=str, help='App ID of the affected app (e.g.: "/db/mysql")')
    args.add_argument('--put', type=str, help='Path to the JSON definition of the app to be created (or updated if'
                                              'it exists), or path to the folder with JSONs to be created/updated.')
    args.add_argument('--fullrollback', action='store_true', help='In case of deployment cancellation, '
                                                                  'rollback all apps. (Default: disabled)'
                                                                  '\nSee README.md for more info.')
    args.add_argument('--tag', type=str,
                      help='Docker tag to update the app to; it only updates the tag (Requires --appid)')
    args.add_argument('--restart', action='store_true', help='Rolling-restart the app (Requires --appid)')
    args.add_argument('--inplacerestart', action='store_true', help='Restart the app in-place'
                                                                    '(Requires --appid, **implies downtime**)')
    args.add_argument('--scale', type=int, help='Re-scale an application (Requires --appid)')
    args.add_argument('--instances', action='store_true',
                      help='Get the number of instances of an app (Requires --appid)')
    args.add_argument('--list', action='store_true', help='List all apps and their image tags')
    args.add_argument('--saveapp', type=str, help='Save an app\'s JSON definition')
    args.add_argument('--dumpall', action='store_true', help='Save all applications JSONs to a folder '
                                                             '(default: ./backup_<date>')
    args.add_argument('--version', '-v', help='Show version and exit')
    args.add_argument('--timeout', '-t', type=int, help='Timeout for deployments in minutes')

    return args.parse_args()


if __name__ == '__main__':
    main()
