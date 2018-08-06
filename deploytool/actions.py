import os
import json
import time
from typing import Union

from marathon import MarathonClient, MarathonApp, MarathonHttpError
from utils.events import wait_for_deployment, poll_deployments_for_app
import utils.string_mangling as mangling


def in_place_restart(client: MarathonClient, appid: str, timeout: int):
    pre = client.get_app(appid).instances
    d = client.scale_app(appid, 0)
    wait_for_deployment(client, d, timeout)
    print('Scaled {} down to 0'.format(appid))
    d = client.scale_app(appid, pre)
    wait_for_deployment(client, d, timeout)
    print('{} back at {} again'.format(appid, pre))


def scale_application(client: MarathonClient, appid: str, instances: int, timeout: int):
    d = client.scale_app(appid, instances, force=True)
    wait_for_deployment(client, d, timeout)


def rolling_restart_app(client: MarathonClient, appid: str, timeout: int):
    d = client.restart_app(appid, force=True)
    wait_for_deployment(client, d, timeout)


def put_app(client: MarathonClient, definition: str, fullrollback: bool, timeout: int) -> str:
    rollback_order = None
    if os.path.isdir(definition):
        prompt = input('The path {} is a directory. Deploy applications defined in it?\nType \'YES\''
                       ' to confirm: '.format(definition))
        if prompt == 'YES':
            if fullrollback:
                print('If you cancel any deployment, all previous applications (although successfully deployed) '
                      'will be rolled back to their previous states.\nAre you totally sure?')
                if input('Type \'YES\' to confirm: ') != 'YES':
                    print('Aborting')
                    exit(2)
                rollback_order = []
            defs = os.listdir(definition)
            defs.sort()
            for d in defs:
                if not d.startswith('#') and os.path.isfile(os.path.join(definition, d)):  # Commented files support
                    deployed = put_app(client, os.path.join(definition, d), False)
                    if deployed is False and rollback_order is not None:
                        #  Initiate full rollback!!
                        rollback_order.sort(reverse=True)
                        do_full_rollback(client, rollback_order)
                    if rollback_order is not None:
                        rollback_order.append(deployed)
            return definition
        else:
            print("Aborting")
            exit(2)
    with open(definition) as f:
        j = json.load(f)
    a = MarathonApp.from_json(j)
    appid = a.id if a.id.startswith('/') else '/' + a.id
    if any(filter(lambda x: x.id == appid, client.list_apps())):
        return _update_application(client, a, timeout, definition)
    else:
        return _create_application(client, a, definition)


def _update_application(client: MarathonClient, app: MarathonApp, timeout: int,
                        definition_path: str, do_backup: bool = True) -> Union[str, bool]:
    if do_backup:
        if not os.path.isdir('./backups'):
            os.mkdir('./backups/')
            print('Created backups directory')
        backup = client.get_app(app.id).to_json()
        backup_path = './backups/{}_{}.json'.format(mangling.appid_to_filename(app.id),
                                                    time.strftime("%Y-%m-%d_%H:%M:%S"))
        with open(backup_path, 'w') as f:
            f.write(backup)
            print('\nBacked app into: {}'.format(backup_path))
    else:
        backup_path = ''
    print('Updating app: {} (from: {})'.format(app.id, definition_path))
    d = client.update_app(app.id, app, force=True)
    # TODO: Handle failure
    # Return the deployed backup file to build rollback order, if necessary
    # or False if a user-initiated rollback completed successfully
    return False if not wait_for_deployment(client, d, timeout) else backup_path


def _create_application(client: MarathonClient, app: MarathonApp, definition_path: str,  do_backup: bool = True) -> Union[str, bool]:
    print('\nCreating app: {} (from: {})'.format(app.id, definition_path))
    try:
        app = client.create_app(app.id, app)
        if app is False:
            print('Deployment of {} failed'.format(app.id))
            exit(1)
    except MarathonHttpError as e:
        if e.status_code == 409:
            # If somehow didn't come up before...
            print('Application already exists. Updating...')
            return _update_application(client, app, definition_path)
        print(e)
        exit(1)
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
            with open(each) as f:
                j = json.load(f)
            app = MarathonApp.from_json(j)
            _update_application(client, app, each, False)
        else:
            d = client.delete_app(each, True)
            wait_for_deployment(client, d, timeout)


def get_instances_amount(client: MarathonClient, appid: str) -> int:
    try:
        return client.get_app(appid).instances
    except MarathonHttpError:
        return -1


def update_app_tag(client: MarathonClient, appid: str, new_tag: str, timeout: int):
    app = client.get_app(appid)
    reg, img = mangling.split_image_name(app.container.docker.image)
    img, tag = mangling.split_image_tag(img)
    new_image = mangling.rebuild_image_name(reg, img, new_tag)
    app.container.docker.image = new_image
    d = client.update_app(appid, app, force=True)
    wait_for_deployment(client, d, timeout)


def list_applications(client: MarathonClient) -> list:
    return [(app.id, app.container.docker.image) for app in client.list_apps()]


def save_application(client: MarathonClient, app: Union[MarathonApp, str]):
    raise NotImplementedError


def dump_all_apps(client: MarathonClient):
    raise NotImplementedError
