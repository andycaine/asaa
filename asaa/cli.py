import click

from . import assistant
from . import core


@click.command()
def start():
    prompt = assistant.start()
    while True:
        response = click.prompt(prompt)
        prompt = assistant.process_response(response)


@click.command()
def list_questions():
    for q in core.load_questions():
        click.echo(q)


@click.group()
def cli():
    pass


cli.add_command(start)
cli.add_command(list_questions)
