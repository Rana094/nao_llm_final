# bridge_test.py
# Python 3 file

import subprocess
import os

PYTHON2 = "/home/rana/.pyenv/versions/2.7.18/bin/python"
NAO_SCRIPT = "/home/rana/Projects/nao-project/nao_control.py"

def send_to_nao(command):
    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/rana/nao-sdk/pynaoqi/lib/python2.7/site-packages"

    subprocess.call(
        [PYTHON2, NAO_SCRIPT, command],
        env=env
    )

send_to_nao("sit")