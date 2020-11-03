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

"""Runs SPEC CPU2006 on Charon SSP SPARC emulator.

From the SPEC CPU2006 documentation:
"The SPEC CPU 2006 benchmark is SPEC's next-generation, industry-standardized,
CPU-intensive benchmark suite, stressing a system's processor, memory subsystem
and compiler."

SPEC CPU2006 homepage: http://www.spec.org/cpu2006/
"""

from absl import flags
from perfkitbenchmarker import configs
from perfkitbenchmarker import sample
from perfkitbenchmarker import vm_util
from perfkitbenchmarker.linux_packages import speccpu
from perfkitbenchmarker.linux_packages import speccpu2006


FLAGS = flags.FLAGS

_SPECINT_BENCHMARKS = frozenset([
    'perlbench', 'bzip2', 'gcc', 'mcf', 'gobmk', 'hmmer', 'sjeng',
    'libquantum', 'h264ref', 'omnetpp', 'astar', 'xalancbmk'])
_SPECFP_BENCHMARKS = frozenset([
    'bwaves', 'gamess', 'milc', 'zeusmp', 'gromacs', 'cactusADM',
    'leslie3d', 'namd', 'dealII', 'soplex', 'povray', 'calculix',
    'GemsFDTD', 'tonto', 'lbm', 'wrf', 'sphinx3'])
_SPECCPU_SUBSETS = frozenset(['int', 'fp', 'all'])

flags.DEFINE_enum(
    'spec_cpu_2006_charon_ssp_benchmark_subset', 'int',
    _SPECFP_BENCHMARKS | _SPECINT_BENCHMARKS | _SPECCPU_SUBSETS,
    'Used by the PKB speccpu2006 benchmark. Specifies a subset of SPEC CPU2006 '
    'benchmarks to run.')
flags.DEFINE_enum('spec_cpu_2006_charon_ssp_runtime_metric', 'rate', ['rate', 'speed'],
                  'SPEC test to run. Speed is time-based metric, rate is '
                  'throughput-based metric.')

BENCHMARK_NAME = 'speccpu2006_charon_ssp'
BENCHMARK_CONFIG = """
speccpu2006_charon_ssp:
  description: Runs SPEC CPU2006 on Charon SSP SPARC emulator
  vm_groups:
    default:
      vm_spec: *default_single_core
"""
#
#      disk_spec: *default_50_gb
#"""

ssh_options = '-2 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o PreferredAuthentications=publickey -o PasswordAuthentication=no -o ConnectTimeout=5 -o GSSAPIAuthentication=no -o ServerAliveInterval=30 -o ServerAliveCountMax=10'


def GetConfig(user_config):
  return configs.LoadConfig(BENCHMARK_CONFIG, user_config, BENCHMARK_NAME)


@vm_util.Retry(log_errors=False, poll_interval=1)
def WaitForSSPBootCompletion(benchmark_spec):
  vm = benchmark_spec.vms[0]

  cmd = 'ssh %s -i ~/.ssh/ssp_solaris_rsa root@%s hostname' % (ssh_options, vm.secondary_nic.private_ip_address)
  stdout, _ = vm.RemoteCommand(cmd, retries=1, suppress_warning=True)


def Prepare(benchmark_spec):
  """Installs SPEC CPU2006 on the target vm.

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
        required to run the benchmark.
  """
  vm = benchmark_spec.vms[0]

  cmd = "sudo sed -i 's/mac = 0a:c6:4a:7d:f0:6c/mac = %s/g' /opt/charon-agent/ssp-agent/ssp/sun-4u/BENCH-4U/BENCH-4U.cfg" % vm.secondary_nic.mac_address
  stdout, _ = vm.RemoteCommand(cmd)

  cmd = 'sudo /opt/charon-ssp/run.ssp.sh'
  stdout, _ = vm.RemoteCommand(cmd)
  # assert stdout.strip() == '1234567890'

  WaitForSSPBootCompletion(benchmark_spec)


def Run(benchmark_spec):
  """Runs SPEC CPU2006 on the target vm.

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
        required to run the benchmark.

  Returns:
    A list of sample.Sample objects.
  """
  vm = benchmark_spec.vms[0]

  # version_specific_parameters = []
  # if FLAGS.spec_cpu_2006_charon_ssp_runtime_metric == 'rate':
  #   version_specific_parameters.append(' --rate=%s ' % vm.NumCpusForBenchmark())
  # else:
  #   version_specific_parameters.append(' --speed ')
  # speccpu.Run(vm, 'runspec',
  #             FLAGS.spec_cpu_2006_charon_ssp_benchmark_subset, version_specific_parameters)

  cmd = 'ssh %s -i ~/.ssh/ssp_solaris_rsa root@%s /cpu2006_test.sh' % (ssh_options, vm.secondary_nic.private_ip_address)
  vm.RobustRemoteCommand(cmd)

  metadata = dict()
  metadata['speccpu2006_metadata'] = 'sample'
  return [sample.Sample('speccpu2006_metric', 1337.0, 'sec', metadata)]

  # log_files = []
  # # FIXME(liquncheng): Only reference runs generate SPEC scores. The log
  # # id is hardcoded as 001, which might change with different runspec
  # # parameters. SPEC CPU2006 will generate different logs for build, test
  # # run, training run and ref run.
  # if FLAGS.spec_cpu_2006_charon_ssp_benchmark_subset in _SPECINT_BENCHMARKS | set(['int', 'all']):
  #   log_files.append('CINT2006.001.ref.txt')
  # if FLAGS.spec_cpu_2006_charon_ssp_benchmark_subset in _SPECFP_BENCHMARKS | set(['fp', 'all']):
  #   log_files.append('CFP2006.001.ref.txt')
  # partial_results = FLAGS.spec_cpu_2006_charon_ssp_benchmark_subset not in _SPECCPU_SUBSETS
  #
  # return speccpu.ParseOutput(vm, log_files, partial_results,
  #                            FLAGS.spec_cpu_2006_charon_ssp_runtime_metric)


def Cleanup(benchmark_spec):
  """Cleans up SPEC CPU2006 from the target vm.

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
        required to run the benchmark.
  """
  vm = benchmark_spec.vms[0]

  cmd = 'ssh %s -i ~/.ssh/ssp_solaris_rsa root poweroff &' % ssh_options
  stdout, _ = vm.RemoteCommand(cmd)

  cmd = 'sleep 30'
  stdout, _ = vm.RemoteCommand(cmd)

  speccpu.Uninstall(vm)
