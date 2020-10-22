from .halcyon import Halcyon

def run():  # pragma: no cover
    """Run Halcyon from the command line."""
    prog = Halcyon()
    prog()


if __name__ == '__main__':  # pragma: no cover
    # Support running module as a commandline command.
    # `python -m halcyon [options] [args]`.
    run()
