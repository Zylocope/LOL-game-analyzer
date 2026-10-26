"""Supported training entry point: python -m backend.train."""
from threadpoolctl import threadpool_limits
from .experiment import run


def train_model():
    # Small tabular models run faster without CPU thread oversubscription.
    with threadpool_limits(limits=1):
        return run()


if __name__ == '__main__':
    train_model()
