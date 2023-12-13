from __future__ import annotations
import dataclasses

from ase.constraints import UnitCellFilter
from typing import TYPE_CHECKING

from atomistics.calculators.output import AtomisticsOutput
from atomistics.calculators.wrapper import as_task_dict_evaluator

if TYPE_CHECKING:
    from ase.atoms import Atoms
    from ase.calculators.calculator import Calculator as ASECalculator
    from ase.optimize.optimize import Optimizer
    from atomistics.calculators.interface import TaskName


class ASEExecutor(object):
    def __init__(self, ase_structure, ase_calculator):
        self.structure = ase_structure
        self.structure.calc = ase_calculator

    def get_forces(self):
        return self.structure.get_forces()

    def get_energy(self):
        return self.structure.get_potential_energy()

    def get_stress(self):
        return self.structure.get_stress(voigt=False)


@dataclasses.dataclass
class ASEStaticOutput(AtomisticsOutput):
    forces: callable = ASEExecutor.get_forces
    energy: callable = ASEExecutor.get_energy
    stress: callable = ASEExecutor.get_stress


@as_task_dict_evaluator
def evaluate_with_ase(
    structure: Atoms,
    tasks: list[TaskName],
    ase_calculator: ASECalculator,
    ase_optimizer: Optimizer = None,
    ase_optimizer_kwargs: dict = {},
):
    results = {}
    if "optimize_positions" in tasks:
        results["structure_with_optimized_positions"] = optimize_positions_with_ase(
            structure=structure,
            ase_calculator=ase_calculator,
            ase_optimizer=ase_optimizer,
            ase_optimizer_kwargs=ase_optimizer_kwargs,
        )
    elif "optimize_positions_and_volume" in tasks:
        results[
            "structure_with_optimized_positions_and_volume"
        ] = optimize_positions_and_volume_with_ase(
            structure=structure,
            ase_calculator=ase_calculator,
            ase_optimizer=ase_optimizer,
            ase_optimizer_kwargs=ase_optimizer_kwargs,
        )
    elif "calc_energy" in tasks or "calc_forces" in tasks or "calc_stress" in tasks:
        quantities = []
        if "calc_energy" in tasks:
            quantities.append("energy")
        if "calc_forces" in tasks:
            quantities.append("forces")
        if "calc_stress" in tasks:
            quantities.append("stress")
        return calc_static_with_ase(
            structure=structure, ase_calculator=ase_calculator, quantities=quantities
        )
    else:
        raise ValueError("The ASE calculator does not implement:", tasks)
    return results


def calc_static_with_ase(
    structure,
    ase_calculator,
    quantities=ASEStaticOutput.fields(),
):
    return ASEStaticOutput.get(
        ASEExecutor(ase_structure=structure, ase_calculator=ase_calculator), *quantities
    )


def optimize_positions_with_ase(
    structure, ase_calculator, ase_optimizer, ase_optimizer_kwargs
):
    structure_optimized = structure.copy()
    structure_optimized.calc = ase_calculator
    ase_optimizer_obj = ase_optimizer(structure_optimized)
    ase_optimizer_obj.run(**ase_optimizer_kwargs)
    return structure_optimized


def optimize_positions_and_volume_with_ase(
    structure, ase_calculator, ase_optimizer, ase_optimizer_kwargs
):
    structure_optimized = structure.copy()
    structure_optimized.calc = ase_calculator
    ase_optimizer_obj = ase_optimizer(UnitCellFilter(structure_optimized))
    ase_optimizer_obj.run(**ase_optimizer_kwargs)
    return structure_optimized
