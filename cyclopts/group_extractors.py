import inspect
from typing import TYPE_CHECKING, Callable, Iterable, List, Literal, Optional, Tuple, Union

from attrs import define, field

if TYPE_CHECKING:
    from cyclopts.core import App

from cyclopts.coercion import to_tuple_converter
from cyclopts.group import Group
from cyclopts.parameter import Parameter, get_hint_parameter


def _create_or_append(
    group_mapping: List[Tuple[Group, List[inspect.Parameter]]],
    group: Union[str, Group],
    iparam: inspect.Parameter,
):
    # updates group_mapping inplace.
    if isinstance(group, str):
        group = Group(group)
    elif isinstance(group, Group):
        pass
    else:
        raise TypeError

    for mapping in group_mapping:
        if mapping[0] == group:
            mapping[1].append(iparam)
            break
    else:
        group_mapping.append((group, [iparam]))


def groups_from_function(
    f: Callable,
    default_parameter: Parameter,
    default_group_arguments: Group,
    default_group_parameters: Group,
) -> List[Tuple[Group, List[inspect.Parameter]]]:
    """Get a list of all groups WITH their children populated.

    The exact Group instances are not guarenteeed to be the same.
    """
    group_mapping: List[Tuple[Group, List[inspect.Parameter]]] = [
        (default_group_arguments, []),
        (default_group_parameters, []),
    ]

    # Assign each parameter to a group
    for iparam in inspect.signature(f).parameters.values():
        _, cparam = get_hint_parameter(iparam.annotation, default_parameter=default_parameter)
        if not cparam.parse:
            continue

        if cparam.group:
            for group in cparam.group:
                if (
                    isinstance(group, Group)
                    and group.default_parameter is not None
                    and group.default_parameter.group is not None
                ):
                    # This shouldn't be possible due to ``Group`` internal checks.
                    raise ValueError("Group.default_parameter cannot have a specified group.")
                _create_or_append(group_mapping, group, iparam)
        else:
            if iparam.kind == iparam.POSITIONAL_ONLY:
                _create_or_append(group_mapping, default_group_arguments, iparam)
            else:
                _create_or_append(group_mapping, default_group_parameters, iparam)

    # Remove the empty groups
    group_mapping = [x for x in group_mapping if x[1]]

    return group_mapping


def groups_from_app(app: "App") -> List[Tuple[Group, List["App"]]]:
    group_mapping: List[Tuple[Group, List["App"]]] = [
        (app.default_group_commands, []),
    ]

    for subapp in app._commands.values():
        if subapp.group is None:
            raise NotImplementedError
        pass

    # Remove the empty groups
    group_mapping = [x for x in group_mapping if x[1]]

    return group_mapping