from __future__ import annotations

import os
import re
import warnings
from copy import copy, deepcopy
from typing import TYPE_CHECKING
from inspect import _empty, signature
from collections import OrderedDict

from rich import print  # noqa: A004
from polars import Series, DataFrame
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table, Column

from torchmeter.utils import dfs_task, resolve_savepath, match_polars_type
from torchmeter.config import FlagNameSpace, get_config, dict_to_namespace

if TYPE_CHECKING:
    from typing import Any, Dict, List, Union, Callable, Optional, Sequence, NamedTuple

    from rich.console import Console, RenderableType
    from rich.segment import Segment
    from polars._typing import PolarsDataType
    from polars.series.series import ArrayLike

    from torchmeter.engine import OperationNode

    LAZY_STR_TYPE = Optional[Union[str, Callable[[Dict[str, Any]], str]]]

__all__ = ["render_perline", "TreeRenderer", "TabularRenderer"]
__cfg__ = get_config()


def apply_setting(  # noqa: C901
    obj: Any,
    setting: FlagNameSpace,
    omit: Optional[Union[str, Sequence[str]]] = None,
    **extra_settings,
) -> Any:
    """
    This funtion is to adapt to the third-party library api change,
    and to apply the settings to the given object in place.

    we can not directly use `obj.__dict__.update(settings)`, cause sometime the
    obj does not have a `__dict__` attribute. Additionally, the obj's properties names may have
    no relationship with its initialization parameters.

    Note:
        - important property(such as Tree.children) should be in omit, or it will be reset.
        - although all of this, if we want to omit some arguments, we still need to set omit to
        the inner related attribute name insteat of the initialization parameter name.
    """  # noqa: DOC201, DOC501

    # prepare the setting dict
    if isinstance(setting, FlagNameSpace):
        setting_dict = setting.data_dict.copy()
    elif isinstance(setting, dict):
        setting_dict = setting.copy()
    else:
        raise TypeError(
            f"The `setting` argument should be a `FlagNameSpace` or a `dict`, but got `{type(setting).__name__}`."
        )
    setting_dict.update(extra_settings)

    # prepare all the initialization arguments
    obj_cls = obj.__class__
    variable_position_idx = None
    variable_keyword_argname = None
    init_args: Dict[str, Any] = OrderedDict()
    for arg_idx, (arg_name, arg) in enumerate(signature(obj_cls).parameters.items()):
        arg_type = arg.kind.name

        if arg_type == "VAR_POSITIONAL":
            variable_position_idx = arg_idx
            variable_position_argname = arg_name
            init_args[arg_name] = list(setting_dict.get(arg_name, []))

        elif arg_type == "VAR_KEYWORD":
            variable_keyword_argname = arg_name
            if arg_name in setting_dict:
                init_args[arg_name] = setting_dict[arg_name]
            else:
                init_args[arg_name] = {k: v for k, v in setting_dict.items() if k not in init_args}

        else:
            if arg_name not in setting_dict and arg.default is _empty:
                try:  # try to find the property with same name in the object
                    init_args[arg_name] = getattr(obj, arg_name)
                except AttributeError:  # if not, this argment is required but absent
                    raise RuntimeError(
                        f"A required argument `{arg_name}` unknown, "
                        + f"consider providing it via `{arg_name}=xxx` or adding it to config."
                    )
            init_args[arg_name] = setting_dict.get(arg_name, arg.default)

    # divide the arguments into position and keyword
    if variable_position_idx is not None:
        all_args = tuple(init_args.keys())
        position_args = [init_args[k] for k in all_args[:variable_position_idx]]
        position_args.extend(init_args[variable_position_argname])
        keyword_args = {k: init_args[k] for k in all_args[variable_position_idx + 1 :]}
    else:
        position_args = []
        keyword_args = init_args

    if variable_keyword_argname is not None:
        keyword_args.update(keyword_args[variable_keyword_argname])
        del keyword_args[variable_keyword_argname]

    # initialize a mirror object
    temp_obj = obj_cls(*position_args, **keyword_args)

    # prepare the state dict
    if hasattr(temp_obj, "__dict__"):
        target_state = temp_obj.__dict__
    else:
        all_states = temp_obj.__slots__

        if not isinstance(all_states, (list, tuple, set)):
            all_states = [all_states]
        all_states = [f"_{obj_cls.__name__}{p}" if p.startswith("__") else p for p in all_states]

        target_state = {p: getattr(temp_obj, p) for p in all_states}

    # filt out the omit items from the state dict
    if omit is not None:
        if not isinstance(omit, (str, list, tuple, set)):
            raise TypeError(
                f"The `omit` argument should be a string, a list, a tuple or a set, but got `{type(omit).__name__}`."
            )

        if isinstance(omit, str):
            omit_items = set([omit])
        else:
            if any(not isinstance((inner := _), str) for _ in omit):
                raise TypeError(
                    f"The `omit` argument receives a `{type(omit).__name__}` of `{type(inner).__name__}`, "
                    + "but expect the inner type to be str."
                )
            omit_items = set(omit)
    else:
        omit_items = set()

    target_state = {k: v for k, v in target_state.items() if k not in omit_items}

    # update obj's state with the setting dict
    if hasattr(obj, "__dict__"):
        obj.__dict__.update(target_state)
    else:
        list(map(lambda kv: setattr(obj, kv[0], kv[1]), target_state.items()))  # type: ignore

    # return the origin object
    return obj


def render_perline(renderable: RenderableType) -> None:
    from time import sleep

    from rich import get_console

    time_sep: float = __cfg__.render_interval
    if time_sep < 0:
        raise ValueError(f"The `render_interval` value defined in config must be non-negative, but got `{time_sep}`")

    console: Console = get_console()

    if not time_sep:
        console.print(renderable)

    else:
        lines: List[List[Segment]] = console.render_lines(renderable, new_lines=True)

        # a fake implementation of `rich.print`
        console._buffer_index = 0
        for line in lines:
            console._buffer.extend(line)
            console._check_buffer()
            sleep(time_sep)


class TreeRenderer:
    loop_algebras: str = "xyijkabcdefghlmnopqrstuvwz" + "XYIJKABCDEFGHLMNOPQRSTUVWZ"

    def __init__(self, node: OperationNode) -> None:
        if node.__class__.__name__ != "OperationNode":
            raise TypeError(f"Expected `node` to be an instance of `OperationNode`, but got `{type(node).__name__}`.")

        self.opnode = node

        self.render_unfold_tree: Optional[Tree] = None
        self.render_fold_tree: Optional[Tree] = None

        def default_rpft(attr_dict: Dict[str, Any]) -> str:
            """Must have only one args which accept an attribute dict"""  # noqa: DOC201
            # basic ext of footer in each repeat block
            start_idx = attr_dict["node_id"].split(".")[-1]

            repeat_winsz = attr_dict["repeat_winsz"]
            if repeat_winsz == 1:
                end_idx = int(start_idx) + attr_dict["repeat_time"] - 1
                return f"Where <loop_algebra> ∈ [{start_idx}, {end_idx}]"
            else:
                end_idx = int(start_idx) + attr_dict["repeat_time"] * repeat_winsz - 1
                valid_vals = list(map(str, range(int(start_idx), end_idx, repeat_winsz)))
            return f"Where <loop_algebra> = {', '.join(valid_vals)}"

        self.__rpft: LAZY_STR_TYPE = default_rpft

    @property
    def default_level_args(self) -> FlagNameSpace:
        if not hasattr(self.tree_levels_args, "default"):
            self.tree_levels_args.default = dict_to_namespace({
                "label": "[b gray35](<node_id>) [green]<name>[/green] [cyan]<type>[/]",  # str | Callable
                "style": "tree",
                "guide_style": "light_coral",
                "highlight": True,
                "hide_root": False,
                "expanded": True,
            })
        return self.tree_levels_args.default

    @property
    def tree_levels_args(self) -> FlagNameSpace:
        return __cfg__.tree_levels_args

    @property
    def repeat_block_args(self) -> FlagNameSpace:
        return __cfg__.tree_repeat_block_args

    @property
    def repeat_footer(self) -> LAZY_STR_TYPE:
        return self.__rpft

    @default_level_args.setter  # type: ignore
    def default_level_args(self, custom_args: Dict[str, Any]) -> None:
        if not isinstance(custom_args, dict):
            raise TypeError(
                f"You can only overwrite `{self.__class__.__name__}.default_level_args` with a dict, "
                + f"but got `{type(custom_args).__name__}`."
            )

        valid_setting_keys = set(signature(Tree).parameters.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(
                f"Keys {invalid_keys} is/are not accepted by `rich.tree.Tree`, refer to "
                + "https://rich.readthedocs.io/en/latest/reference/tree.html#rich.tree.Tree "
                + "for valid args."
            )
        self.default_level_args.update(custom_args)

        self.default_level_args.mark_change()

    @tree_levels_args.setter  # type: ignore
    def tree_levels_args(self, custom_args: Dict[Any, Dict[str, Any]]) -> None:
        if not isinstance(custom_args, dict):
            raise TypeError(
                f"You can only overwrite `{self.__class__.__name__}.tree_levels_args` with a dict, "
                + f"but got `{type(custom_args).__name__}`."
            )

        # filt out invalid level definations and invalid display settings
        valid_setting_keys = set(signature(Tree).parameters.keys())
        for level, level_args_dict in custom_args.items():
            # assure level is a non-negative integer, 'default' or 'all'
            level = level.lower()
            if not level.isnumeric() and level not in ("default", "all"):
                warnings.warn(
                    category=UserWarning,
                    message="The `level` key should be numeric, `default` or `all`, "
                    + f"but got `{level}`.This setting will be ignored.",
                )
                continue

            passin_keys = set(level_args_dict.keys())
            invalid_keys = passin_keys - valid_setting_keys
            if invalid_keys:
                raise KeyError(
                    f"Keys {invalid_keys} is/are not accepted by `rich.tree.Tree`, refer to "
                    + "https://rich.readthedocs.io/en/latest/reference/tree.html#rich.tree.Tree "
                    + "for valid args."
                )

            if level == "default":
                self.default_level_args = level_args_dict  # type: ignore
            elif level == "all":
                self.default_level_args = level_args_dict  # type: ignore
                # delete all levels settings
                levels = [level for level in self.tree_levels_args.__dict__ if level.isnumeric()]
                list(map(lambda level: delattr(self.tree_levels_args, level), levels))  # type: ignore
                break
            else:
                self.tree_levels_args.update({level: level_args_dict})

        self.tree_levels_args.mark_change()

    @repeat_block_args.setter  # type: ignore
    def repeat_block_args(self, custom_args: Dict[str, Any]) -> None:
        if not isinstance(custom_args, dict):
            raise TypeError(
                f"You can only overwrite `{self.__class__.__name__}.repeat_block_args` with a dict, "
                + f"but got `{type(custom_args).__name__}`."
            )

        footer_key = list(filter(lambda x: x.lower() == "repeat_footer", custom_args.keys()))
        if footer_key:
            self.repeat_footer = custom_args[footer_key[-1]]  # type: ignore
            del custom_args[footer_key[-1]]

        valid_setting_keys = set(signature(Panel).parameters.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(
                f"Keys {invalid_keys} is/are not accepted by `rich.panel.Panel`, refer to "
                + "https://rich.readthedocs.io/en/latest/reference/panel.html#rich.panel.Panel "
                + "for valid args."
            )
        self.repeat_block_args.update(custom_args)

        self.repeat_block_args.mark_change()

    @repeat_footer.setter  # type: ignore
    def repeat_footer(self, custom_footer: LAZY_STR_TYPE) -> None:
        from inspect import signature

        if callable(custom_footer):
            func_args = signature(custom_footer).parameters

            if not len(func_args):
                res = custom_footer()  # type: ignore
                if not isinstance(res, (type(None), str)):
                    raise RuntimeError(
                        "If `repeat_foot` is a parameterless function, its return value must be `str` or `None`, "
                        + f"but got a result of type `{type(res).__name__}`."
                    )
                self.__rpft = res

            elif len(func_args) == 1:
                self.__rpft = custom_footer

            else:
                raise RuntimeError(
                    "If `repeat_footer` is a parameterized function, "
                    + "it must have exactly one parameter and will accept a `dict` as input, "
                    + f"but there are {len(func_args)} arguments in the passed-in function."
                )

        elif isinstance(custom_footer, (type(None), str)):
            self.__rpft = custom_footer

        else:
            raise RuntimeError(
                "The `repeat_footer` can be None, string, a parameterless function, or a function with one argument, "
                + f"but got `{type(custom_footer).__name__}`."
            )

        self.repeat_block_args.mark_change()

    def resolve_attr(self, attr_val: Any) -> str:
        """
        Function to process the attribute value resolved by regex.

        Args:
            attr_val (Any): The attribute value resolved by regex.

        Returns:
            str: the processed result. Must be a string!
        """
        return str(attr_val)

    def __call__(self) -> Tree:  # noqa: C901
        from rich.rule import Rule
        from rich.console import Group

        fold_repeat: bool = __cfg__.tree_fold_repeat

        copy_tree: OperationNode = deepcopy(self.opnode)

        # task_func for `dfs_task`
        def __render_per_node(subject: OperationNode, pre_res=None) -> None:  # noqa: ANN001, ARG001, C901
            # skip repeat nodes and folded nodes when enable `fold_repeat`
            if fold_repeat and subject._is_folded:
                return None
            if fold_repeat and not subject._render_when_repeat:
                return None

            display_root: Tree = subject.display_root

            level = str(display_root.label)

            # update display setting for the currently traversed node
            target_level_args = getattr(self.tree_levels_args, level, self.default_level_args)

            # resolve label field
            origin_node_id = subject.node_id
            if fold_repeat and int(level) > 1:
                subject.node_id = subject.parent.node_id + f".{subject.node_id.split('.')[-1]}"  # type: ignore
            label = self.__resolve_argtext(text=getattr(target_level_args, 'label', self.default_level_args.label),
                                           attr_owner=subject)  # fmt: skip

            # apply display setting
            apply_setting(obj=display_root, 
                          setting=target_level_args,
                          omit="children",
                          label=label)  # fmt: skip

            if fold_repeat:
                algebra = self.loop_algebras[0]
                use_algebra = False

                if subject.repeat_winsz < 1:
                    raise RuntimeError("You should never change `repeat_winsz` to be less than 1.")
                if subject.repeat_time < 1:
                    raise RuntimeError("You should never change `repeat_time` to be less than 1.")

                # if the repeat body contains more than one operations
                # get a complete copy of the repeat body, so as to render repeat block more conveniently later.
                if subject.repeat_winsz > 1:
                    use_algebra = True

                    repeat_body_tree = Tree(".", hide_root=True)

                    for loop_idx, (node_id, node_name) in enumerate(subject._repeat_body):
                        repeat_op_node: OperationNode = subject.parent.childs[node_id]  # type: ignore

                        # update node_id with a algebraic expression which indicates the loop
                        if level != "1":
                            if loop_idx == 0:
                                repeat_op_node.node_id = repeat_op_node.parent.node_id + f".{algebra}"  # type: ignore
                            else:
                                repeat_op_node.node_id = repeat_op_node.parent.node_id + f".({algebra}+{loop_idx})"  # type: ignore
                        else:
                            if loop_idx == 0:
                                repeat_op_node.node_id = algebra
                            else:
                                repeat_op_node.node_id = f"{algebra}+{loop_idx}"

                        # resolve label field for the `rich.Tree` object of the currently traversed node
                        label = self.__resolve_argtext(
                            text=getattr(target_level_args, "label", self.default_level_args.label),
                            attr_owner=repeat_op_node,
                        )

                        # update display setting for the `rich.Tree` object of the currently traversed node
                        repeat_display_node: Tree = copy(repeat_op_node.display_root)
                        apply_setting(obj=repeat_display_node,
                                      setting=target_level_args,
                                      omit="children",
                                      label=label)  # fmt: skip

                        # Delete repeat nodes and folded nodes (Note: operate in a copied tree)
                        repeat_display_node.children = [
                            child.display_root
                            for child in repeat_op_node.childs.values()
                            if child._render_when_repeat and not child._is_folded
                        ]

                        repeat_body_tree.children.append(repeat_display_node)

                    display_root = repeat_body_tree
                else:
                    # for the case that the repeat body is only a single operation or the current node is not a
                    # repeat node, just delete its repeat childs or the folded childs and need to do nothing more
                    display_root.children = [
                        child.display_root
                        for child in subject.childs.values()
                        if child._render_when_repeat and not child._is_folded
                    ]

                # render the repeat body as a panel
                if subject.repeat_time > 1:
                    use_algebra = True

                    # update node_id with a algebraic expression which indicates the loop
                    if level != "1":
                        subject.node_id = subject.parent.node_id + f".{algebra}"  # type: ignore
                    else:
                        subject.node_id = algebra
                    display_root.label = self.__resolve_argtext(
                        text=getattr(target_level_args, "label", self.default_level_args.label), 
                        attr_owner=subject
                    )  # fmt: skip

                    block_footer = self.__resolve_argtext(
                        text=self.repeat_footer, attr_owner=subject, 
                        loop_algebra=algebra, node_id=origin_node_id
                    )  # fmt: skip
                    if block_footer:
                        repeat_block_content: Union[Tree, Group] = Group(
                            # the tree structure of the circulating body
                            copy(display_root),
                            # a separator made up of '-'
                            Rule(characters="-", style="dim " + getattr(self.repeat_block_args, "style", "")),
                            # footer
                            "[dim]" + block_footer + "[/]",
                            fit=True,
                        )
                    else:
                        repeat_block_content = copy(display_root)

                    # make a pannel to show repeat information
                    title = self.__resolve_argtext(
                        text=getattr(self.repeat_block_args, "title", ""), 
                        attr_owner=subject, 
                        loop_algebra=algebra
                    )  # fmt: skip

                    repeat_block = apply_setting(
                        obj=Panel(renderable=repeat_block_content),
                        setting=self.repeat_block_args,
                        omit="renderable",
                        title=title,
                        border_style=self.repeat_block_args.border_style + " " + self.repeat_block_args.style,
                    )

                    # overwrite the label of the first node in repeat block
                    subject.display_root.label = repeat_block

                    # remove all children nodes of the first repeat item,
                    # so that only the rendered panel will be displayed
                    subject.display_root.children = []

                if use_algebra:
                    self.loop_algebras = self.loop_algebras[1:] + algebra

            return None

        # apply display setting for each node by dfs traversal
        dfs_task(dfs_subject=copy_tree,
                 adj_func=lambda x: x.childs.values(),
                 task_func=__render_per_node,
                 visited=[])  # fmt: skip

        # cache the rendered result
        if fold_repeat:
            self.render_fold_tree = copy_tree.display_root
        else:
            self.render_unfold_tree = copy_tree.display_root

        return copy_tree.display_root

    def __resolve_argtext(
        self,
        text: LAZY_STR_TYPE,
        attr_owner: "OperationNode",  # type: ignore
        **kwargs,
    ) -> str:
        """
        Disolve all placeholders in form of `<·>` in `text`. If you do not want the content in `<·>` to
        be resolved, you can use `\\<` or `\\>` to escape it. For example, `<name>` will be replaced by
        the value of `attr_owner.name`, while `\\<name\\>` will not be resolved.

        Args:
            text (str): A string that may contain placeholder in the form of `<·>`.
            attr_owner (OperationNode): The object who owns the attributes to be resolved.
            kwargs (dict): Offering additional attributes.

        Returns:
            str: Text with all placeholders resolved.
        """
        attr_dict = copy(attr_owner.__dict__)
        attr_dict.update(kwargs)

        if callable(text):
            text = text(attr_dict)
        elif text is None:
            return ""

        res_str = re.sub(
            pattern=r"(?<!\\)<(.*?)(?<!\\)>",
            repl=lambda match: str(self.resolve_attr(attr_dict.get(match.group(1), None))),
            string=str(text),
        )
        res_str = re.sub(pattern=r"\\<|\\>", repl=lambda x: x.group().replace("\\", ""), string=res_str)
        return res_str


class TabularRenderer:
    def __init__(self, node: OperationNode) -> None:
        if node.__class__.__name__ != "OperationNode":
            raise TypeError(f"Expected `node` to be an instance of `OperationNode`, but got `{type(node).__name__}`.")

        self.opnode = node

        # underlying data
        self.__stats_data: Dict[str, DataFrame] = {stat_name: DataFrame() for stat_name in node.statistics}

    @property
    def stats_data(self) -> Dict[str, DataFrame]:
        return self.__stats_data

    @property
    def tb_args(self) -> FlagNameSpace:
        return __cfg__.table_display_args

    @property
    def col_args(self) -> FlagNameSpace:
        return __cfg__.table_column_args

    @property
    def valid_export_format(self) -> List[str]:
        return ["csv", "xlsx"]

    @tb_args.setter  # type: ignore
    def tb_args(self, custom_args: Dict[str, Any]) -> None:
        if not isinstance(custom_args, dict):
            raise TypeError(
                f"You can only overwrite `{self.__class__.__name__}.tb_args` with a dict, "
                + f"but got `{type(custom_args).__name__}`."
            )

        valid_setting_keys = set(signature(Table).parameters.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(
                f"Keys {invalid_keys} is/are not accepted by `rich.table.Table`, refer to "
                + "https://rich.readthedocs.io/en/latest/reference/table.html#rich.table.Table "
                + "for valid args."
            )
        self.tb_args.update(custom_args)

        self.tb_args.mark_change()

    @col_args.setter  # type: ignore
    def col_args(self, custom_args: Dict[str, Any]) -> None:
        if not isinstance(custom_args, dict):
            raise TypeError(
                f"You can only overwrite `{self.__class__.__name__}.col_args` with a dict, "
                + f"but got `{type(custom_args).__name__}`."
            )

        valid_setting_keys = set(signature(Column).parameters.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(
                f"Keys {invalid_keys} is/are not accepted by `rich.table.Column`, refer to "
                + "https://rich.readthedocs.io/en/latest/reference/table.html#rich.table.Column "
                + "for valid args."
            )
        self.col_args.update(custom_args)

        self.col_args.mark_change()

    def df2tb(self, df: DataFrame, show_raw: bool = False) -> Table:
        # create rich table
        tb_fields = df.columns
        tb = apply_setting(
            obj=Table(*tb_fields),
            setting=self.tb_args,
            omit="columns",
            headers=tb_fields
        )  # fmt: skip

        # apply column settings to all columns
        list(map(lambda tb_col: apply_setting(obj=tb_col, 
                                              omit="header",
                                              setting=self.col_args,
                                              highlight=self.tb_args.highlight), 
                 tb.columns
            )
        )  # fmt: skip

        if df.is_empty():
            return tb

        # collect each column's none replacing string
        col_none_str = {col_name: getattr(df[col_name].drop_nulls()[0], "none_str", "-") 
                        for col_name in df.schema}  # fmt: skip

        # fill table
        for vals_dict in df.iter_rows(named=True):
            str_vals = []
            for col_name, col_val in vals_dict.items():
                if col_val is None:
                    str_vals.append(col_none_str[col_name])
                elif show_raw:
                    str_vals.append(str(getattr(col_val, "raw_data", col_val)))
                else:
                    str_vals.append(str(col_val))

            tb.add_row(*str_vals)

        return tb

    def clear(self, stat_name: Optional[str] = None) -> None:
        if not isinstance(stat_name, (str, type(None))):
            raise TypeError(f"`stat_name` must be a string or None, but got `{type(stat_name).__name__}`.")

        valid_stat_name = self.opnode.statistics
        if isinstance(stat_name, str):
            if stat_name not in valid_stat_name:
                raise ValueError(f"`{stat_name}` not in the supported statistics {valid_stat_name}.")
            self.__stats_data[stat_name] = DataFrame()
        else:
            self.__stats_data = {stat_name: DataFrame() for stat_name in valid_stat_name}

    def export(self, 
               df: DataFrame, 
               save_path: str, 
               file_suffix: str = '',
               ext: Optional[str] = None,
               raw_data: bool = False) -> None:  # fmt: skip
        from polars import List as pl_list
        from polars import Object as pl_object
        from polars import String as pl_str
        from polars import Float64 as pl_float
        from polars import col

        save_path = os.path.abspath(save_path)

        # get save path
        if ext is None:
            ext = os.path.splitext(save_path)[-1]
            if "." not in ext:
                raise ValueError(
                    "File ext unknown! Please specify a path to a file. "
                    + "Or you can specify a file extension using `ext=xxx`, "
                    + f"now we support exporting to {self.valid_export_format} file."
                )

        ext = ext.strip(".")
        if ext not in self.valid_export_format:
            raise ValueError(
                f"`{ext}` file is not supported, now we only support exporting to {self.valid_export_format} file."
            )

        default_filename = f"{self.opnode.name}_{file_suffix}" if file_suffix else self.opnode.name
        _, file_path = resolve_savepath(origin_path=save_path, target_ext=ext, default_filename=default_filename)

        # deal with invalid data
        df = deepcopy(df)

        obj_cols: Dict[str, Any] = {
            col_name: df[col_name].drop_nulls()[0].__class__
            for col_name, col_type in df.schema.items()
            if col_type == pl_object
        }
        df = df.with_columns([
            col(col_name).map_elements(
                lambda s: getattr(s, "raw_data", s.val) if raw_data else str(s),
                return_dtype=pl_float if raw_data else pl_str,
            )
            for col_name in obj_cols
        ])

        # export
        if ext == "csv":
            # list column -> str
            ls_cols = [col_name for col_name, col_type in df.schema.items() if col_type == pl_list]
            df = df.with_columns([
                col(col_name).map_elements(lambda s: str(s.to_list()), return_dtype=pl_str) 
                for col_name in ls_cols
            ])  # fmt: skip
            df.write_csv(file=file_path)

        elif ext == "xlsx":
            df.write_excel(workbook=file_path, autofit=True)

        # output saving message
        if file_suffix:
            print(f"{file_suffix.capitalize()} data saved to [b magenta]{file_path}[/]")
        else:
            print(f"Data saved to [b magenta]{file_path}[/]")

    def __call__(  # noqa: C901
        self,
        stat_name: str,
        *,
        raw_data: bool = False,
        pick_cols: Sequence[str] = [],
        exclude_cols: Sequence[str] = [],
        custom_cols: Dict[str, str] = {},
        keep_custom_name: bool = False,
        newcol_name: str = "",
        newcol_func: Callable[[DataFrame], ArrayLike] = lambda df: [None] * len(df),
        newcol_type: Optional[PolarsDataType] = None,
        newcol_idx: int = -1,
        keep_new_col: bool = False,
        save_to: Optional[str] = None,
        save_format: Optional[str] = None,
    ) -> tuple[Table, DataFrame]:
        """render rich tabel according to the statistics dataframe.
        Note that `pick_cols` work before `custom_col`
        """  # noqa: DOC201, DOC501

        from collections import defaultdict

        if stat_name not in self.opnode.statistics:
            raise ValueError(f"`{stat_name}` not in the supported statistics {self.opnode.statistics}.")
        if not isinstance(newcol_idx, int):
            raise TypeError(f"`newcol_idx` must be an integer, but got `{type(newcol_idx).__name__}`.")
        if not isinstance(pick_cols, (tuple, list, set)):
            raise TypeError(f"`pick_cols` must be a list, tuple or set, but got `{type(pick_cols).__name__}`.")
        if not isinstance(exclude_cols, (tuple, list, set)):
            raise TypeError(f"`exclude_cols` must be a list, tuple or set, but got `{type(exclude_cols).__name__}`.")
        if not isinstance(custom_cols, dict):
            raise TypeError(f"`custom_cols` must be a dict, but got `{type(custom_cols).__name__}`.")

        data: DataFrame = self.__stats_data[stat_name]
        valid_fields = data.columns or getattr(self.opnode, stat_name).tb_fields

        def __fill_cell(subject: OperationNode, pre_res: None = None) -> None:  # noqa: ARG001
            nonlocal val_collector, nocall_nodes, col_sample_data  # type: ignore

            if subject.node_id == "0":
                return

            node_stat = getattr(subject, stat_name)

            try:
                stat_infos: List[NamedTuple] = node_stat.detail_val
                for info_nametuple in stat_infos:
                    info_dict = info_nametuple._asdict()
                    val_collector = {k: val_collector[k] + [v] for k, v in info_dict.items()}

                    if None in col_sample_data.values():
                        col_sample_data = {k: col_sample_data[k] or v 
                                           for k, v in info_dict.items()}  # fmt: skip
            except RuntimeError:
                nocall_nodes.append(f"({subject.node_id}){subject.name}")

        # only when the table is empty, then explore the data using dfs
        if data.is_empty():
            nocall_nodes: List[str] = []
            val_collector: Dict[str, List[Any]] = defaultdict(list)
            col_sample_data: Dict[str, Any] = {col_name: None for col_name in valid_fields}

            dfs_task(dfs_subject=self.opnode,
                     adj_func=lambda x: x.childs.values(),
                     task_func=__fill_cell,
                     visited=[])  # fmt: skip

            if not val_collector:
                raise RuntimeError(
                    f"No {stat_name} data collected, the reasons are three-folds:\n"
                    + "1. No module is called, make sure that your model's `forward` method is not empty.\n"
                    + "2. The whole model is empty and has no sublayers.\n"
                    + "3. You use a single layer as a model, consider putting it in a class and try again.\n"
                )

            col_data: Dict[str, Series] = {
                col_name: Series(name=col_name, values=col_val, dtype=match_polars_type(col_sample_data[col_name]))
                for col_name, col_val in val_collector.items()
            }

            data = DataFrame(data=col_data)
            self.__stats_data[stat_name] = data

            if nocall_nodes:
                warnings.warn(
                    category=RuntimeWarning,
                    message=f"{', '.join(nocall_nodes)}\n"
                    + "The modules above might be defined but not explicitly called. "
                    + "They will be ignored in the measuring, so will not appear in the table below.",
                )

        # pick columns, order defined by `pick_cols`
        if pick_cols:
            invalid_cols = tuple(filter(lambda col_name: col_name not in valid_fields, pick_cols))
            if invalid_cols:
                raise ValueError(f"Column names {invalid_cols} not found in supported columns {data.columns}.")
        else:
            pick_cols = valid_fields
        # not use set is to keep order
        final_cols = [col_name for col_name in pick_cols 
                      if col_name not in exclude_cols]  # fmt: skip
        data = data.select(final_cols)

        # custom columns name, order defined by `custom_col`
        if custom_cols:
            custom_cols = {k: v for k, v in custom_cols.items() if k in final_cols}
            data = data.rename(custom_cols)
            if keep_custom_name:
                self.__stats_data[stat_name] = data

        # add new column
        if newcol_name:
            data = self.__new_col(
                df=data,
                col_name=newcol_name,
                col_func=newcol_func,
                return_type=newcol_type,
                col_idx=newcol_idx,
            )
            if keep_new_col:
                self.__stats_data[stat_name] = data

        tb = self.df2tb(df=data, show_raw=raw_data)

        if save_to:
            save_to = os.path.abspath(save_to)

            # when a dir path is received
            if "." not in os.path.basename(save_to) and save_format not in self.valid_export_format:
                raise ValueError(
                    f"Argument `save_format` must be one in {self.valid_export_format}, but got `{save_format}`. "
                    + "Alternatively, you can set `save_to` to a concrete file path, like `path/to/file.xlsx`"
                )

            self.export(
                df=data,
                save_path=save_to,
                file_suffix=stat_name,
                ext=save_format,
                raw_data=raw_data,
            )

        return tb, data

    def __new_col(
        self,
        df: DataFrame,
        col_name: str,
        col_func: Callable[[DataFrame], ArrayLike],
        return_type: Optional[PolarsDataType] = None,
        col_idx: int = -1,
    ) -> DataFrame:
        from inspect import signature

        # validate col_name
        if not isinstance(col_name, str):
            raise TypeError(f"`col_name` must be a string, but got `{type(col_name).__name__}`.")

        if col_name in df.columns:
            raise ValueError(f"Column name `{col_name}` already exists in the table.")

        # validate col_func
        if not callable(col_func):
            raise TypeError(f"`col_func` must be a callable object, but got `{type(col_func).__name__}`.")
        else:
            col_func_args_num = len(signature(col_func).parameters)
            if col_func_args_num != 1:
                raise TypeError(
                    "`col_func` must take exactly only one argument to receive "
                    + f"the backend dataframe, but got {col_func_args_num} instead."
                )
            else:
                func_ret = col_func(df.clone())
                try:
                    col_data = Series(values=func_ret, dtype=return_type)
                except TypeError:
                    raise TypeError(
                        f"`col_func` must return an array-like object, but got `{type(func_ret).__name__}`."
                    )

                if len(col_data) != len(df):
                    raise RuntimeError(
                        f"The result length of `col_func` is {len(col_data)}, "
                        + f"not matchs the backend dataframe's length {len(df)}."
                    )

        # get new column position
        if col_idx < 0:
            col_idx = len(df.columns) + col_idx + 1 if abs(col_idx) <= len(df.columns) else 0

        final_cols = df.columns[:]
        final_cols.insert(col_idx, col_name)

        # create new column
        return df.with_columns(col_data.alias(col_name)).select(final_cols)
