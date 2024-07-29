import os

import numpy as np
import pandas
import requests
from mendeleev.fetch import fetch_table


def _get_content_from_url(url):
    content = pandas.read_html(requests.get(url).text)
    if len(content[8]) > 1:
        return content[8]
    else:
        return content[9]


def _select_function_density(v):
    if "g/l" in v:
        return float(v.split()[0]) * 0.001
    else:
        return float(v.split()[0])


def _select_function_split(v):
    if isinstance(v, str):
        return float(v.split()[0])
    else:
        return v


def _select_function_lattice(v):
    return (
        float(v.split(", ")[0]),
        float(v.split(", ")[1]),
        float(v.split(", ")[2].split()[0]),
    )


def _select_function_scientific(v):
    if isinstance(v, str):
        return float(v.split()[0].replace("×10", "E"))
    else:
        return v


def _extract_entry(df, n):
    for i in range(int(len(df.columns) / 2)):
        if n in df[i].values:
            v = df[i + 1].values[df[i].values.tolist().index(n)]
            return v


def _default_filter(v):
    return (isinstance(v, str) and "N/A[note]" not in v) or isinstance(v, float)


def _poisson_filter(v):
    return v is not None and not np.isnan(v)


def _select_function_poisson(v):
    return v


def _select_function_mass(v):
    if isinstance(v, str):
        return float(v.replace("[note]", ""))
    else:
        return v


def _extract_lst(df, column, select_function, current_filter):
    element_lst, property_lst = [], []
    try:
        ptable = fetch_table("elements")
        for n, el in zip(ptable.name.values, ptable.symbol.values):
            v = _extract_entry(df=df, n=n)
            if current_filter(v):
                element_lst.append(el)
                property_lst.append(select_function(v))
    except ValueError:
        raise ValueError(column, el, v)
    return element_lst, property_lst


def _collect(url, column, select_function, current_filter):
    return pandas.DataFrame(
        {
            n: d
            for n, d in zip(
                ["element", column],
                _extract_lst(
                    df=_get_content_from_url(url=url),
                    column=column,
                    select_function=select_function,
                    current_filter=current_filter,
                ),
            )
        }
    )


def _get_volume(lat_lst, crystal):
    if not isinstance(lat_lst, float) and len(lat_lst) == 3:
        if crystal == "Face-centered Cubic":
            return lat_lst[0] * lat_lst[1] * lat_lst[2] / 100 / 100 / 100
        elif crystal == "Body-centered Cubic":
            return lat_lst[0] * lat_lst[1] * lat_lst[2] / 100 / 100 / 100
        elif crystal == "Simple Hexagonal":
            return (
                lat_lst[0]
                * lat_lst[1]
                * lat_lst[2]
                * 3
                * np.sqrt(3)
                / 2
                / 100
                / 100
                / 100
            )
        else:
            return None
    else:
        return None


data_dict = {
    "thermalcondictivity": {
        "url": "https://periodictable.com/Properties/A/ThermalConductivity.an.html",
        "select_function": _select_function_split,
        "current_filter": _default_filter,
    },
    "atomicradius": {
        "url": "https://periodictable.com/Properties/A/AtomicRadius.an.html",
        "select_function": _select_function_split,
        "current_filter": _default_filter,
    },
    "bulkmodulus": {
        "url": "https://periodictable.com/Properties/A/BulkModulus.an.html",
        "select_function": _select_function_split,
        "current_filter": _default_filter,
    },
    "shearmodulus": {
        "url": "https://periodictable.com/Properties/A/ShearModulus.an.html",
        "select_function": _select_function_split,
        "current_filter": _default_filter,
    },
    "youngmodulus": {
        "url": "https://periodictable.com/Properties/A/YoungModulus.an.html",
        "select_function": _select_function_split,
        "current_filter": _default_filter,
    },
    "poissonratio": {
        "url": "https://periodictable.com/Properties/A/PoissonRatio.an.html",
        "select_function": _select_function_poisson,
        "current_filter": _poisson_filter,
    },
    "density": {
        "url": "https://periodictable.com/Properties/A/Density.an.html",
        "select_function": _select_function_density,
        "current_filter": _default_filter,
    },
    "liquiddensity": {
        "url": "https://periodictable.com/Properties/A/LiquidDensity.an.html",
        "select_function": _select_function_split,
        "current_filter": _default_filter,
    },
    "thermalexpansion": {
        "url": "https://periodictable.com/Properties/A/ThermalExpansion.an.html",
        "select_function": _select_function_scientific,
        "current_filter": _default_filter,
    },
    "meltingpoint": {
        "url": "https://periodictable.com/Properties/A/AbsoluteMeltingPoint.an.html",
        "select_function": _select_function_scientific,
        "current_filter": _default_filter,
    },
    "vaporizationheat": {
        "url": "https://periodictable.com/Properties/A/VaporizationHeat.an.html",
        "select_function": _select_function_split,
        "current_filter": _default_filter,
    },
    "specificheat": {
        "url": "https://periodictable.com/Properties/A/SpecificHeat.an.html",
        "select_function": _select_function_split,
        "current_filter": _default_filter,
    },
    "latticeconstant": {
        "url": "https://periodictable.com/Properties/A/LatticeConstants.an.html",
        "select_function": _select_function_lattice,
        "current_filter": _default_filter,
    },
    "crystal": {
        "url": "https://periodictable.com/Properties/A/CrystalStructure.an.html",
        "select_function": _select_function_poisson,
        "current_filter": _default_filter,
    },
    "volmolar": {
        "url": "https://periodictable.com/Properties/A/MolarVolume.an.html",
        "select_function": _select_function_scientific,
        "current_filter": _default_filter,
    },
    "mass": {
        "url": "https://periodictable.com/Properties/A/AtomicMass.an.html",
        "select_function": _select_function_mass,
        "current_filter": _default_filter,
    },
}


def _wolframalpha_download():
    result = pandas.concat(
        [
            _collect(
                url=v["url"],
                column=k,
                select_function=v["select_function"],
                current_filter=v["current_filter"],
            ).set_index("element")
            for k, v in data_dict.items()
        ],
        axis=1,
        sort=False,
    )
    result["volume"] = result.apply(
        lambda x: _get_volume(lat_lst=x.latticeconstant, crystal=x.crystal), axis=1
    )
    data_path = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_path, exist_ok=True)
    result.to_csv(os.path.join(data_path, "wolfram.csv"))


def get_chemical_information_from_wolframalpha(chemical_element):
    """
    Get information of a given chemical element
    Args:
        chemical_element: Chemical Element like Au for Gold
    Returns:
        dict: Dictionary with the following keys
            element: chemical element
            thermalcondictivity: thermal conductivity
            atomicradius: calculated distance from nucleus of outermost electron
            bulkmodulus: bulk modulus (incompressibility)
            shearmodulus: shear modulus of solid
            youngmodulus: Young's modulus of solid
            poissonratio: Poisson ratio of solid
            density: density at standard temperature and pressure
            liquiddensity: liquid density at melting point
            thermalexpansion: linear thermal expansion coefficient
            meltingpoint: melting temperature in kelvin
            vaporizationheat: latent heat for liquid-gas transition
            specificheat: specific heat capacity
            latticeconstant: crystal lattice constants
            crystal: basic crystal lattice structure
            volmolar: molar volume
            mass: average atomic weight in atomic mass units
            volume: Volume
    """
    filename = os.path.join(os.path.dirname(__file__), "data", "wolfram.csv")
    if not os.path.exists(filename):
        _wolframalpha_download()
    df = pandas.read_csv(filename)
    return df[df.element == chemical_element].squeeze(axis=0).to_dict()
