#!/usr/bin/env bash

set -xe

MYDIR="$(cd "$(dirname "$0")"; pwd -P)"
recipe_dir="recipe"

source ${MYDIR}/set_env_vars.sh

if [ -n "${TRAVIS}" ];then
    source ci_support/setup_conda.sh
fi

if [ -n "${CIRCLECI}" ];then
    . $HOME/miniconda/etc/profile.d/conda.sh
    conda activate eman
fi

python -m compileall -q -x .git .

if [ -n "$JENKINS_HOME" ];then
    export CPU_COUNT=4
else
    export CPU_COUNT=2
fi

conda info -a
conda list
conda list --explicit
conda render ${recipe_dir}
#conda build purge-all

conda build ${recipe_dir} -c cryoem -c defaults -c conda-forge
