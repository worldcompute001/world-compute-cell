import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from world_compute_cell.cameras import Camera, discover
from world_compute_cell.config import add, load, save
from world_compute_cell.main import main
from world_compute_cell import runtime


class CameraCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {'XDG_CONFIG_HOME':str(self.root/'config'), 'XDG_CACHE_HOME':str(self.root/'cache')})
        self.env.start(); self.addCleanup(self.env.stop)
        self.camera = Camera('/dev/video7','Example USB Camera','usb-test','available')

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = main(['cell', *args])
        return result, out.getvalue()+err.getvalue()

    def test_discovery_prefers_stable_path_and_skips_metadata(self):
        devices = self.root/'dev'; devices.mkdir()
        (devices/'video0').touch(); (devices/'video1').touch()
        stable = devices/'v4l/by-id'; stable.mkdir(parents=True)
        (stable/'usb-example').symlink_to(devices/'video0')
        with patch('world_compute_cell.cameras.query',side_effect=[('Example','usb-x',True),('Metadata','usb-x',False)]):
            cameras=discover(devices,self.root/'sys')
        self.assertEqual(len(cameras),1)
        self.assertEqual(cameras[0].device,str(stable/'usb-example'))

    def test_setup_saves_selected_camera_and_launches_without_ros_commands(self):
        with patch('world_compute_cell.main.require_linux'), patch('world_compute_cell.main.discover',return_value=[self.camera]):
            code, output=self.invoke(['cameras','setup','--device','/dev/video7','--name','desk','--fps','10'])
            self.assertEqual(code,0,output)
            self.assertEqual(load()['cameras']['desk']['model'],'Example USB Camera')
            with patch('world_compute_cell.main.run_ros') as launch, patch('world_compute_cell.main.wait_foreground',return_value=0):
                self.assertEqual(self.invoke(['cameras','start'])[0],0)
            args=launch.call_args.args[0]
            self.assertIn('device:=/dev/video7',args)
            self.assertIn('camera_name:=desk',args)
            self.assertIn('fps:=10.0',args)

    def test_duplicate_and_invalid_setup_do_not_overwrite_config(self):
        data=load();add(data,'desk',self.camera,15);save(data)
        original=load()
        for name,fps in [('desk',15),('side',15),('bad/name',15),('new',float('nan'))]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):add(data,name,self.camera,fps)
        self.assertEqual(load(),original)

    def test_identity_change_never_launches(self):
        data=load();add(data,'desk',self.camera,15);save(data)
        other=Camera('/dev/video7','Different Camera','other','available')
        with patch('world_compute_cell.main.require_linux'),patch('world_compute_cell.main.discover',return_value=[other]),patch('world_compute_cell.main.run_ros') as launch:
            code,output=self.invoke(['cameras','start','desk'])
            self.assertEqual(code,1);self.assertIn('identity changed',output)
            launch.assert_not_called()

    def test_empty_inventory_and_corrupt_config_are_actionable(self):
        with patch('world_compute_cell.main.require_linux'),patch('world_compute_cell.main.discover',return_value=[]):
            code,output=self.invoke(['cameras','setup'])
            self.assertEqual(code,1);self.assertIn('No Linux cameras',output)
        p=self.root/'bad.json';p.write_text('{broken')
        with self.assertRaisesRegex(ValueError,'Cannot read camera configuration'):load(p)

    def test_remove_only_selected_configuration(self):
        data=load();add(data,'desk',self.camera,15);save(data)
        self.assertEqual(self.invoke(['cameras','remove','desk'])[0],0)
        self.assertEqual(load()['cameras'],{})

    def test_unattended_setup_requires_choice(self):
        with patch('world_compute_cell.main.require_linux'),patch('world_compute_cell.main.discover',return_value=[self.camera]),patch('sys.stdin.isatty',return_value=False):
            code,output=self.invoke(['cameras','setup'])
            self.assertEqual(code,1);self.assertIn('--device and --name',output)
            self.assertEqual(load()['cameras'],{})

    def test_ros_wrapper_quotes_arguments_and_sets_local_discovery(self):
        with patch.object(Path,'exists',return_value=True),patch('world_compute_cell.runtime.subprocess.Popen') as popen:
            runtime.run_ros(['echo','a; touch /tmp/should-not-run'])
        command=popen.call_args.args[0][2]
        self.assertIn("'a; touch /tmp/should-not-run'",command)
        self.assertEqual(popen.call_args.kwargs['env']['ROS_AUTOMATIC_DISCOVERY_RANGE'],'LOCALHOST')
        self.assertNotIn('ROS_STATIC_PEERS',popen.call_args.kwargs['env'])


if __name__=='__main__':unittest.main()
