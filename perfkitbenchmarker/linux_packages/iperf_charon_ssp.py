# Copyright 2014 PerfKitBenchmarker Authors. All rights reserved.
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


"""Module containing iperf installation and cleanup functions."""

import posixpath

from perfkitbenchmarker import errors
from perfkitbenchmarker import linux_packages
from perfkitbenchmarker import vm_util

PACKAGE_NAME = 'iperf_charon_ssp' # Should be same as related BENCHMARK_NAME
PACKAGE_DATA = ['iperf2.solaris']
IPERF_BIN = 'iperf2.solaris'

ssh_options = '-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no '\
              '-o IdentitiesOnly=yes -o PreferredAuthentications=publickey '\
              '-o PasswordAuthentication=no -o GSSAPIAuthentication=no '\
              '-o ServerAliveInterval=30 -o ServerAliveCountMax=10 '\
              '-o ConnectTimeout=5 -2 -i ~/.ssh/ssp_solaris_rsa'


def _Install(vm):
  """Installs the iperf package on the VM."""

  vm.InstallPreprovisionedBenchmarkData(PACKAGE_NAME,
                                        PACKAGE_DATA,
                                        vm_util.VM_TMP_DIR)

  scp_cmd = 'scp %s -i ~/.ssh/ssp_solaris_rsa %s root@%s:/iperf'\
            % (ssh_options,
               posixpath.join(vm_util.VM_TMP_DIR, 'iperf2.solaris'),
               vm.secondary_nic.private_ip_address)

  stdout, _ = vm.RemoteCommand(scp_cmd)

  ssh_prefix = 'ssh %s root@%s'\
               % (ssh_options, vm.secondary_nic.private_ip_address)

  stdout, _ = vm.RemoteCommand("%s 'chmod +x /iperf'" % ssh_prefix)


def YumInstall(vm):
  """Installs the iperf package on the VM."""
  _Install(vm)


def AptInstall(vm):
  """Installs the iperf package on the VM."""
  _Install(vm)
