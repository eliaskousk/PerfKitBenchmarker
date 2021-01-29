# Copyright 2019 PerfKitBenchmarker Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing installation functions for SPEC CPU 2000."""

from absl import flags
from perfkitbenchmarker.linux_packages import speccpu

FLAGS = flags.FLAGS

_PACKAGE_NAME = 'speccpu2000_charon_ssp'

INSTALL_DIR = '/export/home/'

_CPU2000_DIR = INSTALL_DIR + 'cpu2000'

_CPU2000_DEFAULT_RUNSPEC_CONFIG = 'solaris-sparc-sun_studio-starter'

_CPU2000_MOUNT_DIR = 'cpu2000_mnt' # Unused for now
_CPU2000_ISO = 'cpu2000-1.2.iso'  # Unused for now
_CPU2000_TAR = 'cpu2000v1.2.tgz'  # Unused for now
_CPU2000_TAR_REQUIRED_MEMBERS = 'cpu2000', 'cpu2000/bin/runspec'  # Unused for now

_LOG_FORMAT = r'Est. (SPEC.*_base2000)\s*(\S*)'

# This benchmark can be run with an .iso file in the data directory, a tar file
# in the data directory, or a tar file preprovisioned in cloud storage. To run
# this benchmark with tar file preprovisioned in cloud storage, update the
# following dict with sha256sum of the file in cloud storage.
PREPROVISIONED_DATA = {_CPU2000_TAR: None}  # Unused for now


def GetSpecInstallConfig(install_dir):
  """Returns a SpecInstallConfigurations() for SPEC CPU 2000.

  Args:
    install_dir: The install directory on the Solaris vdisk that SPEC is installed on.
  """
  install_config = speccpu.SpecInstallConfigurations()
  install_config.package_name = _PACKAGE_NAME
  install_config.log_format = _LOG_FORMAT
  install_config.charon_ssp = True

  install_config.base_spec_dir = _CPU2000_DIR
  install_config.runspec_config = (FLAGS.runspec_config or
                                   _CPU2000_DEFAULT_RUNSPEC_CONFIG)
  install_config.base_mount_dir = _CPU2000_MOUNT_DIR
  install_config.base_iso_file_path = _CPU2000_ISO
  install_config.base_tar_file_path = _CPU2000_TAR
  install_config.required_members = _CPU2000_TAR_REQUIRED_MEMBERS

  install_config.UpdateConfig(install_dir)
  return install_config


def Install(vm):
  """Installs SPECCPU 2000."""
  speccpu.InstallSPECCPU(vm, GetSpecInstallConfig(INSTALL_DIR))
