# SPDX-License-Identifier: MIT
"""One service of each role per local user and broker port (Linux)."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path

@contextmanager
def single_instance(role, port):
    base=Path(os.environ.get('XDG_RUNTIME_DIR',str(Path.home()/'.cache')))/'sameloop'
    base.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (base/f'{port}-{role}.lock').open('a') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f'Un service {role} utilise déjà ce broker pour cet utilisateur') from None
        yield
