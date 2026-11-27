"""Smoke-test a pip-installed wheel from outside the source checkout."""
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import world_compute_cell
from world_compute_cell.runtime import prepare_workspace

repository = Path(__file__).resolve().parents[1]
assert not Path(world_compute_cell.__file__).resolve().is_relative_to(repository), 'Test the installed wheel, not the checkout'
assert world_compute_cell.__version__ == importlib.metadata.version('world-compute-cell')
cli = Path(sys.executable).parent / 'world-compute'
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    os.environ['XDG_CONFIG_HOME'] = str(root/'config')
    os.environ['XDG_DATA_HOME'] = str(root/'data')
    for args in [['--version'],['cell','--help'],['cell','cameras','--help'],['cell','cameras','configured']]:
        subprocess.run([str(cli),*args],cwd=root,check=True)
    workspace = prepare_workspace()
    for name in ['package.xml','setup.py','setup.cfg','resource/world_compute_camera',
                 'world_compute_camera/reader.py','world_compute_camera/node.py']:
        assert (workspace/'src/world_compute_camera'/name).is_file(), name
print('PASS: installed command and bundled runtime work outside the checkout')
