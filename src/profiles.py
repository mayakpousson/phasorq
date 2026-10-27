"""Versioned, illustrative five-qubit devices for repeatable lessons."""

from dataclasses import dataclass

import pandas as pd
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import InstructionProperties
from qiskit.transpiler.target import QubitProperties


EDGES = tuple((a, b) for a in range(4) for b in (a + 1,)) + tuple(
    (b, a) for a in range(4) for b in (a + 1,)
)


@dataclass(frozen=True)
class HardwareProfile:
    key: str
    name: str
    description: str
    version: str
    t1_us: tuple[float, ...]
    t2_us: tuple[float, ...]
    one_qubit_error: tuple[float, ...]
    readout_error: tuple[float, ...]
    two_qubit_error: tuple[float, ...]  # Adjacent pairs 0-1 through 3-4.


PROFILES = {
    "uniform": HardwareProfile(
        "uniform", "Uniform quality", "Five qubits with similar, modest synthetic errors.", "1",
        (100.,) * 5, (80.,) * 5, (.001,) * 5, (.02,) * 5, (.01,) * 4,
    ),
    "uneven": HardwareProfile(
        "uneven", "Uneven quality", "Some qubits and links are substantially noisier.", "1",
        (120., 45., 110., 95., 40.),
        (100., 30., 90., 85., 25.),
        (.0005, .006, .001, .0015, .007),
        (.01, .06, .015, .02, .07),
        (.03, .03, .007, .04),
    ),
}


def build_backend(profile: HardwareProfile) -> GenericBackendV2:
    """Keep compilation properties and Aer noise derived from the same target."""
    backend = GenericBackendV2(num_qubits=5, coupling_map=list(EDGES), seed=42)
    target = backend.target
    qubit_properties = list(target.qubit_properties)
    for qubit in range(5):
        qubit_properties[qubit] = QubitProperties(
            t1=profile.t1_us[qubit] * 1e-6,
            t2=profile.t2_us[qubit] * 1e-6,
            frequency=5e9,
        )
        for name in ("sx", "x", "id"):
            target.update_instruction_properties(name, (qubit,), InstructionProperties(
                duration=50e-9, error=profile.one_qubit_error[qubit]
            ))
        target.update_instruction_properties("rz", (qubit,), InstructionProperties(
            duration=0., error=0.
        ))
        target.update_instruction_properties("measure", (qubit,), InstructionProperties(
            duration=1e-6, error=profile.readout_error[qubit]
        ))
        target.update_instruction_properties("reset", (qubit,), InstructionProperties(
            duration=1e-6, error=profile.readout_error[qubit]
        ))
    target.qubit_properties = qubit_properties
    for a, b in EDGES:
        target.update_instruction_properties("cx", (a, b), InstructionProperties(
            duration=300e-9, error=profile.two_qubit_error[min(a, b)]
        ))
    return backend


def telemetry_frame(profile: HardwareProfile) -> pd.DataFrame:
    return pd.DataFrame({
        "qubit_id": range(5),
        "t1_us": profile.t1_us,
        "t2_us": profile.t2_us,
        "gate_error_rate": profile.one_qubit_error,
    })
