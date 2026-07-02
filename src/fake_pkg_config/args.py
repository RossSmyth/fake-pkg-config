import argparse
from sys import stderr
from typing import Literal

ActionName = Literal["store", "store_true", "append", "store_const"]


def order_action(action: type[argparse.Action] | ActionName) -> type[argparse.Action]:
    """Factory that returns an argparse.Action that ignores the flag if it comes
    after some certain flags, and stores the order flags came in
    """
    super_class: type[argparse.Action]

    # We need to store an uninstanced class
    match action:
        case "store":
            super_class = argparse._StoreAction
        case "store_true":
            super_class = argparse._StoreTrueAction
        case "store_const":
            super_class = argparse._StoreFalseAction
        case "append":
            super_class = argparse._AppendAction
        case str(name):
            raise ValueError(f"Invalid action: '{name}'")
        case cls if issubclass(cls, argparse.Action):
            super_class = cls
        case other:
            raise ValueError(f"Invalid Action: {other}")

    class EnforceOrderAction(super_class):
        """Must disabe flags if they come after certain other flags"""

        disabled_by: list[str] = []

        def __init__(self, disabled_by: list[str], **kwargs):
            self.disabled_by = disabled_by

            super().__init__(**kwargs)

        def __call__(
            self,
            _: argparse.ArgumentParser,
            namespace: argparse.Namespace,
            values,
            option_string=None,
        ):
            # Check if the namespace already has any of the attrs it is disabled by on it
            parsed_incompat = any(hasattr(namespace, name) for name in self.disabled_by)

            if parsed_incompat:
                print(
                    f"{option_string} is incompatible with previous flags, ignoring",
                    file=stderr,
                )
            else:
                arg_queue = getattr(namespace, "arg_queue", [])
                namespace.arg_queue = arg_queue.append(self.dest)
                setattr(namespace, self.dest, values)

    return EnforceOrderAction


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fake pkg-config that always reports libraries exist",
    )

    parser.add_argument(
        "--libs",
        action=order_action("store_true"),
        disabled_by=["variables", "modversion"],
        help="Get the linker flags for the specified module",
    )
    parser.add_argument(
        "--cflags",
        action=order_action("store_true"),
        disabled_by=["variables", "modversion"],
        help="Get the flags to append to CFLAGS for the specific modules",
    )
    parser.add_argument(
        "--variables",
        action=order_action("append"),
        disabled_by=["libs", "cflags", "modversion"],
        help="Get a variable from the specified modules",
    )
    parser.add_argument(
        "--modversion",
        action=order_action("store_true"),
        disabled_by=["libs", "cflags", "variables"],
        help="Get verion of the specified modules",
    )
    parser.add_argument(
        "libs",
        nargs="*",
        default=[],
        help="All pkg-config modules to query",
    )

    return parser
