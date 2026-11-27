from setuptools import setup
setup(name='world_compute_camera', version='0.1.0', packages=['world_compute_camera'],
      data_files=[('share/ament_index/resource_index/packages', ['resource/world_compute_camera']),
                  ('share/world_compute_camera', ['package.xml'])],
      entry_points={'console_scripts': ['camera_reader = world_compute_camera.reader:main',
                                         'camera_bridge = world_compute_camera.node:main']})
