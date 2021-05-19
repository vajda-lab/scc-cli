import click
import os
import requests
from requests.auth import HTTPBasicAuth
from rich import print as rprint


SCC_API_TOKEN = os.environ.get("SCC_API_TOKEN")
SCC_API_URL = os.environ.get("SCC_API_URL", "http://ftplus.bu.edu:8000/apis")


@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug):
    click.echo("Debug mode is %s" % ("on" if debug else "off"))


@cli.command()
@click.argument("job_id", type=str)
def delete(job_id):
    """
    User will need to run `status` first, to get uuid to use as job_id
    Using job_id (Job.uuid)
    For Django object:
        Set Job.status to STATUS_DELETED
    """

    click.echo("delete")
    # I can't get Job.STATUS_DELETED to work
    data = {}
    try:
        response = requests.delete(
            f"{SCC_API_URL}jobs/{job_id}/",
            data=data,
            auth=HTTPBasicAuth("kojo@revsys.com", "kojo"),
        )
        click.echo(response.status_code)
    except Exception as e:
        click.secho(f"{e}", fg="red")


@cli.command()
def status():
    """
    Shows status of all jobs user is authorized to see
    Draws data from Django app
    Django app updated from SCC, via scheduled_poll_job Celery task
    """
    click.echo("status")
    data = {}
    response = requests.get(
        f"{SCC_API_URL}jobs/",
        data=data,
        auth=HTTPBasicAuth("kojo@revsys.com", "kojo"),
        # auth=HTTPBasicAuth("kojo.idrissa@gmail.com", "BlizzardManBetterThanTPain"),
    )
    print(response.status_code)
    results = response.json()["results"]
    for result in results:
        rprint(result)


# ToDo Will SCC token provide auth for Django app and user_id for submit host?
@cli.command()
@click.argument("input_file", type=click.File("rb"))
def submit(input_file):
    """
    Takes compressed input TAR file, creates job in Django app
    Submission to SCC is handled by scheduled_allocate_job Celery task
    """
    files = {"input_file": input_file}
    click.echo("Submitting")
    data = {}
    response = requests.post(
        f"{SCC_API_URL}jobs/",
        auth=HTTPBasicAuth("kojo@revsys.com", "kojo"),
        data=data,
        files=files,
    )
    print(response.status_code)
    print(response)
    print(response.text)


if __name__ == "__main__":
    cli(obj={})
