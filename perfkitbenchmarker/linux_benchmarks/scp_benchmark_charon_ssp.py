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
"""Runs plain SCP.

Runs SCP on Charon SSP SPARC emulator to collect file transfer throughput.
"""

import logging
import posixpath
import re
from absl import flags
from perfkitbenchmarker import configs
from perfkitbenchmarker import sample
from perfkitbenchmarker import vm_util

FLAGS = flags.FLAGS

BENCHMARK_NAME = 'scp_charon_ssp'

BENCHMARK_CONFIG = """
scp_charon_ssp:
  description: Run scp on Charon SSP SPARC emulator
  vm_groups:
    vm_1:
      vm_spec: *default_single_core
      disk_spec: *default_50_gb
    vm_2:
      vm_spec: *default_single_core
      disk_spec: *default_50_gb
"""


def GetConfig(user_config):
  return configs.LoadConfig(BENCHMARK_CONFIG, user_config, BENCHMARK_NAME)


def Prepare(benchmark_spec):
  """Install iperf and start the server on all machines.

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
      required to run the benchmark.
  """
  vms = benchmark_spec.vms
  if len(vms) != 2:
    raise ValueError(
        f'scp benchmark requires exactly two machines, found {len(vms)}')


@vm_util.Retry(max_retries=1)
def _RunSCP(sending_vm, receiving_vm, receiving_ip_address, ip_type):
  """Run iperf using sending 'vm' to connect to 'ip_address'.

  Args:
    sending_vm: The VM sending traffic.
    receiving_vm: The VM receiving traffic.
    receiving_ip_address: The IP address of the iperf server (ie the receiver).
    ip_type: The IP type of 'ip_address' (e.g. 'internal', 'external')

  Returns:
    A Sample.
  """

  metadata = {
      # The meta data defining the environment
      'receiving_machine_type': receiving_vm.machine_type,
      'receiving_zone': receiving_vm.zone,
      'sending_machine_type': sending_vm.machine_type,
      'sending_zone': sending_vm.zone,
      'ip_type': ip_type,
  }

  file_size_str = '512m'
  file_size = 512 * 1024 * 1024

  sending_path = '/export/home/scp_test_file'
  receiving_path = '/export/home/downloads/'
  receiving_location = 'root@%s:%s' % (
    receiving_ip_address, receiving_path)

  mkfile_cmd = 'mkfile %s %s' % (file_size_str, sending_path)
  sending_vm.RemoteCommand("'%s'" % mkfile_cmd, nested=True)

  scp_cmd = ['(', 'time', 'scp', '-P', str(22), '-pr']
  scp_cmd.extend(vm_util.GetCharonSSPNestedSshOptions('/.ssh/id_rsa'))
  scp_cmd.extend([sending_path, receiving_location])
  scp_cmd.append(') 2>&1')
  stdout, _ = sending_vm.RemoteCommand("'%s'" % ' '.join(scp_cmd), nested=True, timeout=120)

  time_match = re.search(
  #    r'^scp_test_file\s+100%\s+(?P<size>\d+\.?\d+)(?P<units>\S+)\s+\d+:\d+$', stdout)
      r'real\s+(?P<minutes>\d+)m(?P<seconds>\d+\.?\d+)s', stdout)
  throughput = 0.0
  if time_match:
    minutes = int(time_match.group('minutes'))
    seconds = (60 * minutes) + float(time_match.group('seconds'))
    throughput = (file_size / (1024 * 1024)) / seconds

  scp_metadata = {
      'file_size': file_size,
  }
  metadata.update(scp_metadata)
  return sample.Sample('Throughput', throughput, 'MBytes/sec', metadata)


def Run(benchmark_spec):
  """Run iperf on the target vm.

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
      required to run the benchmark.

  Returns:
    A list of sample.Sample objects.
  """
  vms = benchmark_spec.vms
  results = []

  logging.info('SCP Results:')

  # Send traffic in both directions
  for sending_vm, receiving_vm in vms, reversed(vms):
    # Send using external IP addresses
    logging.info('Send Using External IPs: %s -> %s' % (sending_vm, receiving_vm))
    if vm_util.ShouldRunOnExternalIpAddress() and FLAGS.aws_dualeips:
      results.append(
          _RunSCP(sending_vm,
                  receiving_vm,
                  receiving_vm.secondary_nic.public_ip_address,
                  vm_util.IpAddressMetadata.EXTERNAL))

    # Send using internal IP addresses
    logging.info('Send Using Internal IPs: %s -> %s' % (sending_vm, receiving_vm))
    if vm_util.ShouldRunOnInternalIpAddress(sending_vm, receiving_vm):
      results.append(
          _RunSCP(sending_vm,
                  receiving_vm,
                  receiving_vm.secondary_nic.private_ip_address,
                  vm_util.IpAddressMetadata.INTERNAL))

  return results


def Cleanup(benchmark_spec):
  """Cleanup iperf on the target vm (by uninstalling).

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
      required to run the benchmark.
  """
  vms = benchmark_spec.vms
  for vm in vms:
    cmd = 'poweroff &'
    stdout, _ = vm.RemoteCommand(cmd, nested=True)

    cmd = 'sleep 20'
    stdout, _ = vm.RemoteCommand(cmd)
