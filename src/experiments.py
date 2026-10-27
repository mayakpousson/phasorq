"""Small, measured circuits with outcomes students can check."""

from dataclasses import dataclass

from qiskit import QuantumCircuit


@dataclass(frozen=True)
class Experiment:
    key: str
    name: str
    question: str
    explanation: str
    expected: dict[str, float]
    measured_bits: int


EXPERIMENTS = {
    "bell": Experiment(
        "bell", "Bell state", "Can two measured bits agree even when each is random?",
        "A Hadamard and controlled-NOT prepare correlated outcomes. In the Z basis, "
        "00 and 11 should each occur about half the time. These counts alone do not prove entanglement.",
        {"00": 0.5, "11": 0.5}, 2,
    ),
    "ghz": Experiment(
        "ghz", "Three-qubit GHZ state", "Can three measured bits move together?",
        "A GHZ circuit prepares 000 and 111 with equal ideal probability. More measurements "
        "reduce sampling variation, but cannot remove device noise.",
        {"000": 0.5, "111": 0.5}, 3,
    ),
    "bv": Experiment(
        "bv", "Bernstein–Vazirani", "Can one circuit reveal a hidden three-bit string?",
        "The oracle encodes 101. An ideal run always measures 101 on the three input bits; "
        "noise may produce other strings.",
        {"101": 1.0}, 3,
    ),
}


def build_circuit(key: str) -> QuantumCircuit:
    """Return a new circuit, with measured classical bits in Qiskit's bit order."""
    if key == "bell":
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])
    elif key == "ghz":
        circuit = QuantumCircuit(3, 3)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        circuit.measure([0, 1, 2], [0, 1, 2])
    elif key == "bv":
        circuit = QuantumCircuit(4, 3)
        circuit.x(3)
        circuit.h(3)
        for bit in range(3):
            circuit.h(bit)
        circuit.cx(0, 3)
        circuit.cx(2, 3)
        for bit in range(3):
            circuit.h(bit)
        circuit.measure([0, 1, 2], [0, 1, 2])
    else:
        raise ValueError(f"Unknown experiment: {key}")
    return circuit


def outcome_distance(counts: dict[str, int], expected: dict[str, float]) -> float:
    """Total variation distance between observed and ideal bitstring distributions."""
    shots = sum(counts.values())
    if shots <= 0 or any(value < 0 for value in counts.values()):
        raise ValueError("Counts must be nonnegative and contain measurements")
    outcomes = set(counts) | set(expected)
    return 0.5 * sum(abs(counts.get(outcome, 0) / shots - expected.get(outcome, 0))
                     for outcome in outcomes)
