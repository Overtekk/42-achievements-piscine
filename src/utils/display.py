"""
Terminal output management utilities.

This module provides a centralized interface for displaying formatted
messages using the Rich library. It manages distinct output streams
(stdout and stderr) to ensure that logs and errors do not interfere with
potential structured outputs.

Attributes:
    standard_console (Console): The default console instance for standard
                                output.
    error_console (Console): A console instance configured specifically for
                             stderr.
"""

from rich.console import Console
from rich.errors import StyleSyntaxError
from rich.style import Style


standard_console: Console = Console()
error_console: Console = Console(stderr=True)


def print_error(message: str) -> None:
    """
    Displays a formatted error message on the standard error stream.

    Args:
        message (str): The specific error description to be displayed.
    """
    prefix: str = "[ERROR]: "
    content: str = f"{message}"
    error_console.print(f"[bold red]{prefix + content}[/bold red]")


def print_success(message: str) -> None:
    """
    Display a formatted success message on the standard stream.

    Args:
        message (str): The specific message to be displayed.
    """
    standard_console.print(f"[green]{message}[/green]")


def print_warn(message: str) -> None:
    """
    Display a formatted warn message on the standard error stream.

    Args:
        message (str): The specific warning message to be displayed.
    """
    prefix: str = "[WARNING]: "
    content: str = f"{message}"
    error_console.print(f"[bold yellow]{prefix + content}[/bold yellow]")


def print_log(message: str) -> None:
    """
    Display a formatted log message on the standard stream using 'log' from
    rich. Using '_stack_offset' allow good naming for the file.

    Args:
        message (str): The specific message to be displayed.
    """
    standard_console.log(message, _stack_offset=2)


def print_rule(message: str, color: str = "bold blue") -> None:
    """
    Display a horizontal rule with a message at the center and with a
    specific color. If the color doesn't exist or isn't specify, the color
    bold blue will by the default color.

    Args:
        message (str): The specific message to be displayed.
        color (str): The color used for the rule.
    """
    style_rule: str = color

    try:
        Style.parse(style_rule)

    except StyleSyntaxError:
        style_rule = "bold blue"
        print_error(f"'{color}' is unkown. Switching to default (bold blue).")

    standard_console.rule(message, style=style_rule)
