from torchmeter import __version__


def main() -> None:
    print(f"Sorry, TorchMeter {__version__} does not support command line interface yet.")
    print(
        "Please use it as a library, or update to the newest version using `pip install -U torchmeter` and try again."
    )


if __name__ == "__main__":
    main()
