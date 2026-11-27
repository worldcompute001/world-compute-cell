import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from world_compute_cell.runtime import BUNDLED_SOURCE, prepare_workspace, workspace_path, ros_environment


class PackageTests(unittest.TestCase):
    def test_bundled_runtime_is_copied_to_user_data_not_installation(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_DATA_HOME':directory}):
            workspace=prepare_workspace()
            self.assertEqual(workspace,workspace_path())
            self.assertTrue(workspace.is_relative_to(directory))
            self.assertFalse(workspace.is_relative_to(BUNDLED_SOURCE))
            package=workspace/'src/world_compute_camera'
            for name in ['setup.py','setup.cfg','package.xml','resource/world_compute_camera',
                         'world_compute_camera/reader.py','world_compute_camera/node.py']:
                self.assertTrue((package/name).is_file(),name)
            self.assertEqual((package/'world_compute_camera/reader.py').read_bytes(),
                             (BUNDLED_SOURCE/'world_compute_camera/reader.py').read_bytes())
            (workspace/'sentinel').write_text('preserve')
            self.assertEqual(prepare_workspace(),workspace)
            self.assertEqual((workspace/'sentinel').read_text(),'preserve')

    def test_runtime_uses_system_python_even_when_cli_is_in_virtualenv(self):
        with patch.dict(os.environ,{'VIRTUAL_ENV':'/tmp/example-venv','PYTHONPATH':'/tmp/unrelated',
                                    'PYTHONHOME':'/tmp/unrelated','PATH':'/tmp/example-venv/bin'}):
            env=ros_environment()
        for key in ['VIRTUAL_ENV','PYTHONPATH','PYTHONHOME']:
            self.assertNotIn(key,env)
        self.assertTrue(env['PATH'].startswith('/usr/bin:/bin:'))

if __name__=='__main__':unittest.main()
