[![Travis build status](https://travis-ci.org/nicovillanueva/marathon-deployer.svg?branch=master)](https://travis-ci.org/nicovillanueva/marathon-deployer)

# Marathon deployment tool

## Set up

### Development
- Requires Python 3.7 or higher
- Dependencies in `requirements.txt`: `pip3 install -r requirements.txt`
- Use of virtualenv is recommended as always
- For testing against a local cluster you may use [minidcos](https://github.com/dcos/dcos-e2e#minidc-os-cli)

## Options
- `--marathon`: Marathon to connect to. Supports comma-separated hosts: `http://m1:8080,http://m2:8080,http://m3:8080`. Defaults to `http://localhost:8080`.
- `--appid`: Application ID of the app to be affected. Example: `/group1/foo/bar`
- `--put`: May be two values:
    - Path to a single, .json file, containing the definition of a single Marathon application
    - Path to a folder containing a set .json files, each with the definition of a single Marathon application. No recursivity supported. Files starting with '#' are ignored.
    - If the .json refers to a pre-existing application, it will be updated
    - If the application is to be updated, a backup json will be created (in `./backups/{appid}_{date}.json`; `backups` folder will be created if it does not exist)
- `--fullrollback`: If present, the `--put` parameter is set to a folder, and a rollback is performed (read 'Rolling back' below), all previously created/updated apps are rolled back (if updated) or destroyed (if created) in reverse order (last updated/created will be the first to be rolled back/destroyed). If the initial rollback is forced, this 'full rollback' is not performed. 
- `--tag`: Only update the Docker tag of a given `--appid`. As such, only Docker applications are supported.
- `--restart`: Restart an application. It's done in rolling fashion: New instances are created, then old ones taken down. No downtime, but requires enough resources in the cluster to fit `instances_amount * 2` during deployment
- `--inplacerestart`: Scale down and back up an application. Tough way to do a restart: Implies downtime, but has lower resources requirements.
- `--scale`: Scale up/down an application.
- `--instances`: Get the amount of instances an application has.
- `--list`: List all applications in the Marathon cluster and their Docker images/tags
- `--saveapp`: [Not implemented] Save a given application's json
- `--dumpall`: [Not implemented] Save all applications' jsons

## Rolling back
Most operations on Marathon imply a 'Deployment'. Whether is the creation, update, destruction, or restart of an app.

In most cases (except on creation, for now) these deployments can be cancelled (Ctrl+C while waiting for it to finish). When cancelling a deployment, _a new deployment is created_ (the one to roll back to the previous state).

When cancelling a deployment, an option is given: To let it flow (the new rollback-deployment is created) or to force the cancellation (the deployment is killed, and the affected app is left as-is; this is dangerous and the application must be manually controlled afterwards).  
If the cancellation is not forced, in turn, this 'rollback-deployment' cannot be cancelled: they are triggered and are not waited for completion, we just move on.

When using the `--fullrollback` parameter, upon *forcefully* cancelling a deployment (triggered by a .json read from the folder given with the `--put` parameter), the rest of the applications are not rolled back. The script just exits and a manual rollback must be performed (the backup jsons may come in handy here).  
If you do *not* force the cancellation (let the rollback deployment flow), the rest of the applications will be rolled back, in the inverse order they were created/updated.

### Rollback workflow

![alt text](deployment-flow.png "Deployment flow")

## Release new version

To release a new version, with a valid `~/.pypirc` configured for authentication:

1. Have Twine installed: `pip install twine`
2. Edit the version number in `marathon_deploy/version.py`
3. Run `python setup.py sdist` to build a new package
4. (Optional) Install it locally using `pip install dist/marathon-deploy-$(cat marathon_deploy/version.py).tar.gz`
5. Run `twine upload dist/*`
6. Make the appropiate changes to the `CHANGELOG.md`
6. Commit the new version to Git: `git add CHANGELOG.MD marathon_deploy/version.py && git commit -am "Version $(cat marathon_deploy/version.py)" && git tag $(cat marathon_deploy/version.py) && git push --tags`

## TODO
- Verify if the target app is a Docker container when using `--tag`
- Support cancellation of the creation of an app
- Assume `yes` (unattended)
- On failed deployment, show last task failure message (stderr)
- BUG: --list blows up when there are non-Docker apps in Marathon
- BUG: Ordering is broken with 10> apps (ordering as string, so, for example, `19` goes before `2`)
