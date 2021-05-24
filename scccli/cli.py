import click
import os
import requests
from requests.auth import AuthBase, HTTPBasicAuth
from rich import print as rprint


SCC_API_TOKEN = os.environ.get("SCC_API_TOKEN")
SCC_API_URL = os.environ.get("SCC_API_URL", "http://ftplus.bu.edu:8000/apis/")
SCC_API_USER = os.environ.get("SCC_API_USER")
SCC_API_PASSWORD = os.environ.get("SCC_API_PASSWORD")


class TokenAuth(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        """Attach an API token to a custom auth header."""
        request.headers["X-TokenAuth"] = f"{self.token}"
        return request


def get_auth():

    if SCC_API_TOKEN:
        return TokenAuth(SCC_API_TOKEN)
    elif SCC_API_USER and SCC_API_PASSWORD:
        return HTTPBasicAuth(SCC_API_USER, SCC_API_PASSWORD)
    else:
        click.secho(
            "please default (SCC_API_USER and SCC_API_PASSWORD) or SCC_API_TOKEN"
        )


@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug):
    click.echo("Debug mode is %s" % ("on" if debug else "off"))
    if debug:
        click.echo(f"SCC_API_URL: {SCC_API_URL}")
        click.echo(f"SCC_API_USER: {SCC_API_USER}")
        click.echo(
            "SCC_API_PASSWORD is %s" % ("set" if SCC_API_PASSWORD else "not set")
        )
        click.echo("SCC_API_TOKEN is %s" % ("set" if SCC_API_TOKEN else "not set"))


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
            auth=get_auth(),
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
    try:
        response = requests.get(
            f"{SCC_API_URL}jobs/",
            data=data,
            auth=get_auth(),
        )
        print(response.status_code)
        results = response.json()["results"]
        rprint(f"YOU HAVE {len(results)} RESULTS:")
        for result in results:
            rprint(result)

    except requests.exceptions.ConnectionError as e:
        click.secho(f"{e}", fg="red")


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
    try:
        response = requests.post(
            f"{SCC_API_URL}jobs/",
            auth=get_auth(),
            data=data,
            files=files,
        )
        print(response.status_code)
        print(response)
        print(response.text)

    except requests.exceptions.ConnectionError as e:
        click.secho(f"{e}", fg="red")


if __name__ == "__main__":
    cli(obj={})
