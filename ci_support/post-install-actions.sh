#!/usr/bin/env bash

set -xe

source ${PREFIX}/bin/activate

conda config --env --set auto_update_conda False

mkdir ${PREFIX}/install_logs

conda info -a            | tee ${PREFIX}/install_logs/info_log.txt 2>&1
conda list               | tee ${PREFIX}/install_logs/list_log.txt 2>&1
conda list --explicit | tee -a ${PREFIX}/install_logs/list_log.txt 2>&1

case ${EMAN_INSTALL_DONT_UPDATE_DEPS:-} in
    0|"")
        conda install eman-deps=24.1 -c cryoem -c defaults -c conda-forge -y | tee -a ${PREFIX}/install_logs/install_log.txt 2>&1
        ;;
    *)
        echo "WARNING: Skipping installation of dependencies per user request..."
        ;;
esac

set +x

python <<ENDPATCH
import platform
import sys
import site
from pathlib import Path
from subprocess import run


def is_python_patched():
    py_ver = platform.python_version_tuple()
    
    return int(py_ver[0]) >= 3 and (   int(py_ver[1]) >= 8 and int(py_ver[2]) >= 8
                                    or int(py_ver[1]) >= 9 and int(py_ver[2]) >= 1)

print("\n\nPatching PyOpenGL for 'macOS Big Sur'? ... ", end='')


file_to_patch =  Path(site.getsitepackages()[0]) / 'OpenGL/platform/ctypesloader.py'
patch='''
@@ -76,7 +76,7 @@ def _loadLibraryWindows(dllType, name, mode):
     """
     fullName = None
     try:
-        fullName = util.find_library( name )
+        fullName = '/System/Library/Frameworks/' + name + '.framework/' + name
         if fullName is not None:
             name = fullName
         elif os.path.isfile( os.path.join( DLL_DIRECTORY, name + '.dll' )):
'''

if platform.mac_ver()[0] == '10.16' and not is_python_patched():
    print("yes")
    run(['patch', str(file_to_patch),], input=patch, text=True)
else:
    print("no")
ENDPATCH

cat <<EOF

INSTALLATION IS NOW COMPLETE

Please, go to http://blake.bcm.edu/emanwiki/EMAN2/Install/BinaryInstallAnaconda
for detailed installation instructions, testing and troubleshooting information.
If this installation is on a Linux cluster,
you will require additional steps before installation is complete!

EOF
