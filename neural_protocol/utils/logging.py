import logging

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(name)-12s | %(message)s",
        datefmt="%H:%M:%S"
    )