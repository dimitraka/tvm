# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Verilator utility functions"""

import sys

import tvm
from tvm import relay
import tvm.relay.testing
from tvm import runtime
from tvm.relay import transform


def _register_verilator_op(op_name, supported=True):
    """The helper function to indicate that a given operator can be supported by Verilator.

    Paramters
    ---------
    op_name : Str
        The name of operator that will be registered.

    Returns
    -------
    f : callable
        A function that returns if the operator is supported by DNNL.
    """

    @tvm.ir.register_op_attr(op_name, "target.verilator")
    def _func_wrapper(expr):
        return supported

    return _func_wrapper


def skip_test():
    """Skip test if it requires the Verilator codegen and it's not present."""
    if not tvm.get_global_func("relay.ext.verilator", True):
        print("Skip test because Verilator codegen is not available.")
        return True
    if sys.platform == "win32":
        print("Skip test on Windows for now")
        return True
    return False


def offload(mod):
    """Offload ops based on the registered ops"""

    backend = "verilator"
    mod = transform.AnnotateTarget([backend])(mod)
    mod = transform.PartitionGraph()(mod)
    return mod


def compile_module(mod):
    """Compile Relay module"""

    with relay.build_config(opt_level=3):
        exe = relay.vm.compile(mod, target="llvm", params=None)
        code, lib = exe.save()
        return runtime.vm.Executable.load_exec(code, lib)


def run_module(exe, inputs):
    """Run Relay module"""

    ctx = tvm.cpu()
    vm = runtime.vm.VirtualMachine(exe, ctx)
    return vm.run(**inputs)
