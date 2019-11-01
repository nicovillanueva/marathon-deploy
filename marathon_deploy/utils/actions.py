import os
import json
import sys
import time
from typing import Union
from itertools import takewhile

from marathon import MarathonClient, MarathonApp, MarathonHttpError
from marathon_deploy.utils.events import wait_for_deployment, poll_deployments_for_app


def in_place_restart(client: MarathonClient, appid: str):
    pre = client.get_app(appid).instances
    deployment = client.scale_app(appid, 0)
    wait_for_deployment(client, deployment)
    print('Scaled {} down to 0'.format(appid))
    deployment = client.scale_app(appid, pre)
    wait_for_deployment(client, deployment)
    print('{} back at {} again'.format(appid, pre))


def put_app(client: MarathonClient, definition_path: str, fullrollback: bool) -> str:
    rollback_order = None
    if os.path.isdir(definition_path):
        prompt = input('The path {} is a directory. Deploy applications defined in it?\nType \'YES\''
                       ' to confirm: '.format(definition_path))
        if prompt != 'YES':
            print("Aborting")
            sys.exit(2)
        if fullrollback:
            print('If you cancel any deployment, all previous applications (although successfully deployed) '
                  'will be rolled back to their previous states.\nAre you totally sure?')
            if input('Type \'YES\' to confirm: ') != 'YES':
                print('Aborting')
                sys.exit(2)
            rollback_order = []
        for definition_filename in sorted(os.listdir(definition_path)):
            definition_filepath = os.path.join(definition_path, definition_filename)
            if not definition_filename.startswith('#') and os.path.isfile(definition_filepath):  # Commented files support
                deployed = put_app(client, definition_filepath, False)
                if deployed is False and rollback_order is not None:
                    #  Initiate full rollback!!
                    rollback_order.sort(reverse=True)
                    do_full_rollback(client, rollback_order)
                if rollback_order is not None:
                    rollback_order.append(deployed)
        return definition_path
    with open(definition_path) as json_file:
        app = MarathonApp.from_json(json.load(json_file))
    appid = app.id if app.id.startswith('/') else '/' + app.id
    if any(filter(lambda x: x.id == appid, client.list_apps())):
        return _update_application(client, app, definition_path)
    return _create_application(client, app, definition_path)


def _update_application(client: MarathonClient, app: MarathonApp,
                        definition_path: str, do_backup: bool = False) -> Union[str, bool]:
    if do_backup:
        if not os.path.isdir('./backups'):
            os.mkdir('./backups/')
            print('Created backups directory')
        backup = client.get_app(app.id).to_json()
        if app.id.startswith('/'):
            appid = appid[1:]
        appid = appid.replace('/', '_').replace('.', '')
        backup_path = './backups/{}_{}.json'.format(appid,
                                                    time.strftime("%Y-%m-%d_%H:%M:%S"))
        with open(backup_path, 'w') as backup_file:
            backup_file.write(backup)
            print('\nBacked app into: {}'.format(backup_path))
    else:
        backup_path = ''
    print('Updating app: {} (from: {})'.format(app.id, definition_path))
    deployment = client.update_app(app.id, app, force=True)
    # TODO: Handle failure
    # Return the deployed backup file to build rollback order, if necessary
    # or False if a user-initiated rollback completed successfully
    if not wait_for_deployment(client, deployment):
        client.restart_app(app.id)
    return False if not wait_for_deployment(client, deployment) else backup_path


def _create_application(client: MarathonClient, app: MarathonApp, definition_path: str) -> Union[str, bool]:
    print('\nCreating app: {} (from: {})'.format(app.id, definition_path))
    try:
        app = client.create_app(app.id, app)
        if app is False:
            print('Deployment of {} failed'.format(app.id))
            sys.exit(1)
    except MarathonHttpError as error:
        if error.status_code == 409:
            # If somehow didn't come up before...
            print('Application already exists. Updating...')
            return _update_application(client, app, definition_path)
        raise error
    # TODO: Migrate to `wait_for_deployment`
    # Return the deployed appid to build rollback order, if necessary
    # or False if the creation was cancelled
    return False if not poll_deployments_for_app(client, app) else app.id


def do_full_rollback(client: MarathonClient, rollback: list):
    print('------------------\nPerforming rollback in order:')
    print('\n'.join(rollback))
    print('------------------')
    for each in rollback:
        if os.path.isfile(each):
            with open(each) as json_file:
                app = MarathonApp.from_json(json.load(json_file))
            _update_application(client, app, each, False)
        else:
            deployment = client.delete_app(each, True)
            wait_for_deployment(client, deployment)


def get_instances_amount(client: MarathonClient, appid: str) -> int:
    try:
        return client.get_app(appid).instances
    except MarathonHttpError:
        return -1


def _replace_tag_version(imagename: str, new_tag: str) -> str:
    tagname = list(takewhile(lambda x: x != ':', imagename[::-1]))[::-1]
    if '/' in tagname:
        return f"{imagename}:{new_tag}"
    return imagename.replace(''.join(tagname), new_tag)


def update_docker_tag(client: MarathonClient, appid: str, new_tag: str):
    app = client.get_app(appid)
    if app.container.type != 'DOCKER':
        print('Only docker images can be retagged')
        return
    new_imagename = _replace_tag_version(app.container.docker.image, new_tag)
    app.container.docker.image = new_imagename
    deployment = client.update_app(appid, app, force=True)
    wait_for_deployment(client, deployment)


def list_applications(client: MarathonClient) -> list:
    return [(app.id, app.container.docker.image) for app in client.list_apps()]


def save_application(client: MarathonClient, app: Union[MarathonApp, str]):
    raise NotImplementedError


def dump_all_apps(client: MarathonClient):
    raise NotImplementedError
