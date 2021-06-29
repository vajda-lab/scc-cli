import click
import logging
import json
import os
import requests

from pathlib import Path
from requests.auth import AuthBase, HTTPBasicAuth
from rich import print as rprint
from rich.console import Console
from rich.table import Table
import time


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SCC_API_PASSWORD = os.environ.get("SCC_API_PASSWORD")
SCC_API_TOKEN = os.environ.get("SCC_API_TOKEN")
SCC_API_URL = os.environ.get("SCC_API_URL", "http://ftplus.bu.edu:8000/apis/")
SCC_API_USER = os.environ.get("SCC_API_USER")


class TokenAuth(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        """Attach an API token to a custom auth header."""
        request.headers["Authorization"] = f"Token {self.token}"
        # request.headers["WWW-Authenticate"] = f"{self.token}"
        return request


def get_auth():
    config_file = Path(os.path.expanduser("~"), ".config", "scc-cli.json")
    if config_file.exists():
        config = json.loads(config_file.read_text())
    else:
        rprint(
            f"Your authorization token is not properly configured.\nPlease create an account at {SCC_API_URL} to get an access token.\nThen return here and run the 'init' command to assign that token to yourself."
        )
        config = {}

    if SCC_API_TOKEN or config.get("SCC_API_TOKEN"):
        return TokenAuth(SCC_API_TOKEN or config.get("SCC_API_TOKEN"))

    elif SCC_API_USER and SCC_API_PASSWORD:
        return HTTPBasicAuth(SCC_API_USER, SCC_API_PASSWORD)

    else:
        click.secho(
            "please default (SCC_API_USER and SCC_API_PASSWORD) or SCC_API_TOKEN"
        )


def unauthorized_user_message():
    """
    A simple string that may change over time.
    Placed here to make code a bit "dryer"
    """
    return f"\nCurrently, you are not authorized to connect.\nPlease create an account at {SCC_API_URL} to get an access token.\nThen return here and run the 'init' command to assign that token to yourself."


@click.group()
@click.option("--debug/--no-debug", default=False)
def click_group(debug):
    # click.echo("Debug mode is %s" % ("on" if debug else "off"))

    if debug:
        click.echo(f"SCC_API_URL: {SCC_API_URL}")
        click.echo(f"SCC_API_USER: {SCC_API_USER}")
        click.echo(
            "SCC_API_PASSWORD is %s" % ("set" if SCC_API_PASSWORD else "not set")
        )
        click.echo("SCC_API_TOKEN is %s" % ("set" if SCC_API_TOKEN else "not set"))


@click_group.command()
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
        if response.status_code == 401:
            rprint(unauthorized_user_message())
        logger.debug(response.status_code)
    except Exception as e:
        click.secho(f"{e}", fg="red")


@click_group.command()
@click.argument("access_token", type=str)
def init(access_token):
    click.echo("Adding our token")

    # find our home folder and store our config
    config_path = Path(os.path.expanduser("~"), ".config")
    if not config_path.exists():
        config_path.mkdir()

    config_file = config_path.joinpath("scc-cli.json")

    # If our config exists, load our config
    if config_file.exists():
        config = json.loads(config_file.read_text())
    else:
        config = {}

    # Add our token to the config file
    config["SCC_API_TOKEN"] = access_token
    config_file.write_text(json.dumps(config, indent=2))

    # Update file permission so that students can't see each others tokens
    mask = oct(os.stat(config_file).st_mode)[-3:]
    if mask != "600":
        config_file.chmod(0o600)


def build_status_output_table(results_data):
    """
    Take list of dictionaries built from Job.job_data objects
    Return Rich.Table to be paginated in status() command
    """
    table = Table(title="QSTAT Results")
    table.add_column("q_status")
    table.add_column("job-ID")
    table.add_column("prior")
    table.add_column("name")
    table.add_column("user")
    table.add_column("state")
    table.add_column("submit-start-at")
    table.add_column("queue")
    table.add_column("slots")
    table.add_column("ja-task-ID")

    for result in results_data:
        table.add_row(
            result.get("status"),
            result.get("job-ID"),
            result.get("prior"),
            result.get("name"),
            str(result.get("user")),
            result.get("state"),
            result.get("submit-start-at"),
            result.get("queue"),
            result.get("slots"),
            result.get("ja-task-ID"),
        )

    return table


@click_group.command()
@click.option("--job_id", "-j", type=str, required=False)
@click.option("--uuid", type=str, required=False)
def status(job_id, uuid):
    """
    Shows status of all jobs user is authorized to see
    Draws data from Django app
    Django app updated from SCC, via scheduled_poll_job Celery task
    """
    data = {}
    console = Console()

    try:
        if job_id:
            response = requests.get(
                f"{SCC_API_URL}jobs/",
                data=data,
                auth=get_auth(),
            )
            if response.status_code == 401:
                rprint(unauthorized_user_message())
            else:
                results = response.json()["results"]
                matched_result = [
                    result["job_data"]
                    for result in results
                    if result["sge_task_id"] == int(job_id)
                ]
            # Explicit no result message
            if len(matched_result) > 0:
                rprint(matched_result[0])
            else:
                rprint("[red]No matching result found[/red]")
        elif uuid:
            response = requests.get(
                f"{SCC_API_URL}jobs/{uuid}",
                data=data,
                auth=get_auth(),
            )
            if response.status_code == 401:
                rprint(unauthorized_user_message())
            else:
                results = response.json()
                rprint("\nIf [cyan]status[/cyan] = queued [bold]and[/bold] [cyan]job_data[/cyan] = {}, this job hasn't been sent to the SCC yet.")
                rprint(results)
        else:
            response = requests.get(
                f"{SCC_API_URL}jobs/",
                data=data,
                auth=get_auth(),
            )
            if response.status_code == 401:
                rprint(unauthorized_user_message())
            else:
                results = response.json()["results"]
                results_data = []
                for result in results:
                    item = result.copy()
                    item.update(**result["job_data"])
                    logger.debug(item)
                    results_data.append(item)
                results_table = build_status_output_table(results_data)

                # Usage instructions
                rprint(
                    f"""YOU HAVE {len(results_data)} RESULTS
                        \n[bright_green]WHEN RESULTS DISPLAY:[/bright_green]
                        \nPress [bold cyan]SPACE[/bold cyan] for next page of results
                        \nPress [bold cyan]Q[/bold cyan] to quit.
                    """
                )

                console.input(
                    "[bright_green]To SKIP INSTRUCTIONS[/bright_green] and go straight to your results:\nPress [bold cyan]Enter/Return[/bold cyan]: "
                )

                with console.pager():
                    console.print(results_table)
    except requests.exceptions.ConnectionError as e:
        click.secho(f"{e}", fg="red")


# ToDo Will SCC token provide auth for Django app and user_id for submit host?
@click_group.command()
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
        if response.status_code == 401:
            rprint(unauthorized_user_message())
        else:
            click.echo("Submitted")
        logger.debug(response.status_code)
        logger.debug(response)
        logger.debug(response.text)
        uuid = response.json()["uuid"]
        rprint(f"Submitted job UUID: {uuid}")

    except requests.exceptions.ConnectionError as e:
        click.secho(f"{e}", fg="red")


if __name__ == "__main__":
    click_group(obj={})
