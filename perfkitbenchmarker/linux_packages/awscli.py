# Copyright 2016 PerfKitBenchmarker Authors. All rights reserved.
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

"""Package for installing the AWS CLI."""

from perfkitbenchmarker import errors


def Install(vm):
  """Installs the awscli package on the VM."""

  # For AWS CLI v1
  vm.InstallPackages('python3-pip')
  vm.RemoteCommand('sudo pip3 install awscli')

  # For AWS CLI v2
  # vm.InstallPackages('curl unzip')
  # vm.RemoteCommand("curl \"https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip\" -o \"awscliv2.zip\"")
  # vm.RemoteCommand('unzip awscliv2.zip')
  # vm.RemoteCommand('sudo ./aws/install')


def YumInstall(vm):
  """Installs the awscli package on the VM."""
  # amazon linux 2 has awscli pre-installed. Check to see if it exists and
  # install it if it does not.
  try:
    vm.RemoteCommand('yum list installed awscli')
  except errors.VirtualMachine.RemoteCommandError:
    Install(vm)


def Uninstall(vm):
  # For AWS CLI v1
  vm.RemoteCommand('/usr/bin/yes | sudo pip3 uninstall awscli')

  # For AWS CLI v2
  # vm.RemoteCommand('rm -f awscliv2.zip && rm -rf aws/')
