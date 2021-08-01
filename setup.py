# SPDX-FileCopyrightText: 2021 Number6174
# SPDX-License-Identifier: Apache-2.0

from distutils.core import setup
import py2exe

setup(
    options = {
        'py2exe': {
            'bundle_files': 1, # Bundle into as few files as possible
            'optimize': 2, # Apply more optimizations
            'includes': ['pynput.keyboard._win32', 'pynput.mouse._win32'],
            'excludes': ['doctest', 'pdb', 'unittest', 'difflib', 'inspect'],
            'compressed': True,
        }
    },
    data_files = [('.', ['config.json', 'config.json.license', 'control_panel.html', 'README.md']),
                  ('examples', ['examples/timer.html', 'examples/clock.png', 'examples/clock.png.license']),
                  ('LICENSES', ['LICENSES/CC0-1.0.txt', 'LICENSES/Apache-2.0.txt'])],
    console=['server.py']
)