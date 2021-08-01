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
    data_files = [('.', ['config.json', 'control_panel.html', 'README.md', 'LICENSE']),
                  ('examples', ['examples/timer.html', 'examples/clock.png'])],
    console=['server.py']
)