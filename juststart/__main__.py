#!/usr/bin/env python3

import logging

from .main import main


def run():
    logging.basicConfig(level=logging.INFO)
    main()


if __name__ == "__main__":
    run()
