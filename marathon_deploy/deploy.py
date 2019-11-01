#!/usr/bin/env python3

import sys
import time
import marathon_deploy.utils.actions as actions
from marathon import MarathonClient

import click

# Hide urllib warnings for insecure certificates
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import warnings

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

@click.group()
@click.option('--urls', default='http://localhost:8080/', show_default=True, help='Comma-separated Marathon URLs to target')
@click.option('--insecure', is_flag=True, help='Skip HTTPS checks')
@click.option('--auth', help='Marathon authentication (username:password)')
def cli(auth: str, urls: str, insecure: bool):
    user, password = auth.split(':') if auth is not None else ("", "")
    servers = urls.split(",")
    client = MarathonClient(
        servers=servers,
        username=user,
        password=password,
        verify=not insecure,
    )
    if client.ping().strip().decode() != '"pong"':
        click.echo(f"could not connect to Marathon at {urls}")
        sys.exit(1)
    ctx = click.get_current_context()
    ctx.obj = {}
    ctx.obj['client'] = client


@cli.command()
@click.argument('app_path')
@click.option('--fullrollback', is_flag=True)
def put(app_path: str, fullrollback: bool):
    actions.put_app(click.get_current_context().obj['client'], app_path, fullrollback)


@cli.command()
@click.argument('app_id')
@click.argument('app_version')
def tag(app_id, app_version):
    client = click.get_current_context().obj['client']
    actions.update_docker_tag(client, app_id, app_version)


@cli.command()
@click.argument('app_id')
@click.option('--inplace', is_flag=True, help='Scale down and up again')
def restart(app_id, inplace):
    click.echo(f"restarting {app_id} (in place: {inplace})")
    client = click.get_current_context().obj['client']
    if inplace:
        actions.in_place_restart(client, app_id)
        return
    deployment = client.restart_app(app_id, force=True)
    actions.wait_for_deployment(client, deployment)


# BUG: marathon.exceptions.MarathonHttpError: MarathonHttpError: HTTP 422 returned with message, "Invalid JSON"
@cli.command()
@click.argument('app_id')
@click.argument('count')
def scale(app_id, count):
    click.echo(f"scaling {app_id} to {count}")
    client = click.get_current_context().obj['client']
    client.scale_app(app_id, count, force=True)


@cli.command('instances')
@click.argument('app_id')
def instance_count(app_id):
    click.echo(f"fetching count of app {app_id}")
    client = click.get_current_context().obj['client']
    print(actions.get_instances_amount(client, app_id))


# TODO: implement
@cli.command()
@click.argument('app_id')
def dump(app_id):
    click.echo(f'dumping app {app_id}')
    client = click.get_current_context().obj['client']
    actions.save_application(client, app_id)


# TODO: implement
@cli.command('dumpall')
def dump_all():
    click.echo('dumping all')
    client = click.get_current_context().obj['client']
    actions.dump_all_apps(client)


@cli.command('staged')
@click.argument('app_id')
def deploy_in_progress(app_id):
    client = click.get_current_context().obj['client']
    staged = client.get_app(app_id).tasks_staged
    while staged > 0:
        click.echo(f"App {app_id} in staging mode")
        time.sleep(1)
        staged = client.get_app(app_id).tasks_staged
