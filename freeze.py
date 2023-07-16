# SPDX-FileCopyrightText: 2023 Number6174
# SPDX-License-Identifier: Apache-2.0

from py2exe import freeze

freeze(
    options={
        'bundle_files': 1,  # Bundle into as few files as possible
        'optimize': 2,  # Apply more optimizations
        'includes': ['pynput.keyboard._win32', 'pynput.mouse._win32'],
        'excludes': ['doctest', 'pdb', 'unittest', 'difflib', 'inspect'],
        'compressed': True,
    },
    data_files=[('.', ['config.json', 'config.json.license', 'control_panel.html', 'favicon.ico', 'favicon.ico.license',
                       'README.md']),
                ('examples', ['examples/timer.html', 'examples/clock.png', 'examples/clock.png.license']),
                ('LICENSES', ['LICENSES/CC0-1.0.txt', 'LICENSES/Apache-2.0.txt'])],
    console=[{'script': 'server.py', 'icon_resources': [(1, 'favicon.ico')]}]
)
