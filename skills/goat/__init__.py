"""Goat skills."""

import importlib
from dataclasses import is_dataclass
from typing import (
    Any,
    Dict,
    Literal,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from eth_account import Account
from eth_account.signers.local import LocalAccount
from goat.classes.plugin_base import PluginBase
from goat_adapters.langchain import get_on_chain_tools
from goat_wallets.web3 import Web3EVMWalletClient
from web3 import Web3
from web3.middleware.signing import SignAndSendRawMiddlewareBuilder

from abstracts.skill import SkillStoreABC
from skills.goat.base import GoatBaseTool


def resolve_optional_type(field_type: Type) -> Type:
    if hasattr(field_type, "__origin__") and get_origin(field_type) is Union:
        args = get_args(field_type)
        if (
            type(None) in args and len(args) == 2
        ):  # Check if None is one of the types in Union and there are 2 types
            return next(t for t in args if t is not type(None))
    return field_type


def resolve_type(val: str, mod) -> Any:
    try:
        return getattr(mod, val)
    except AttributeError:
        try:
            mod_path, cls_name = val.rsplit(".", 1)
            type_mod = importlib.import_module(mod_path)
            return getattr(type_mod, cls_name)
        except (ValueError, ImportError, AttributeError) as e:
            raise ValueError(f"type '{val}' could not be resolved") from e


def resolve_value(val: Any, f_type: Type, mod) -> Any:
    f_type = resolve_optional_type(f_type)

    if f_type in (str, int, float, bool):
        return f_type(val)

    if hasattr(f_type, "__origin__"):
        if f_type.__origin__ is list:
            if not isinstance(val, list):
                raise ValueError(f"expected list object but got {type(val).__name__}")

            elem_type = f_type.__args__[0]
            return [resolve_value(item, elem_type, mod) for item in val]
        if f_type.__origin__ is Literal:
            literal_items = f_type.__args__
            if val not in literal_items:
                raise ValueError(f"not supported literal value {type(val)}")

            return val

    if isinstance(val, str):
        return resolve_type(val, mod)

    raise ValueError(f"unsupported type: {f_type}")


def get_goat_skill(
    private_key: str,
    plugin_configs: Dict[str, Any],
    rpc_node: str,
    skill_store: SkillStoreABC,
    agent_store: SkillStoreABC,
    agent_id: str,
) -> list[GoatBaseTool]:
    if not private_key:
        raise ValueError("GOAT private key is empty")

    if not rpc_node:
        raise ValueError("GOAT rpc node is empty")

    plugins = {}
    for p_name, p_options in plugin_configs.items():
        try:
            mod = importlib.import_module(f"goat_plugins.{p_name}")

            initializer = getattr(mod, p_name)
            hints = get_type_hints(initializer)

            opt_type = hints.get("options")
            if not opt_type:
                raise ValueError(
                    f"GOAT plugin {p_name} does not have associated options"
                )

            opt_type = resolve_optional_type(opt_type)
            if not is_dataclass(opt_type):
                raise ValueError(f"GOAT plugin {p_name} options is malformed")

            fields = get_type_hints(opt_type)

            resolved_vals = {}
            raw_args = p_options

            for f_name, f_type in fields.items():
                if f_name not in raw_args:
                    if f_type.__name__.upper() == "OPTIONAL":
                        continue
                    raise ValueError(
                        f"GOAT plugin {p_name} should have {f_name} option"
                    )

                val = raw_args[f_name]

                try:
                    resolved_val = resolve_value(val, f_type, mod)
                    resolved_vals[f_name] = resolved_val

                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"GOAT field {f_name} has invalid value, plugin name {p_name} : {str(e)}"
                    )

            plugin_options = opt_type(**resolved_vals)

            plugin: PluginBase = initializer(options=plugin_options)
            plugins[p_name] = plugin

        except AttributeError:
            raise Exception(f"GOAT initializer function not found: {p_name}")
        except ImportError:
            raise Exception(f"GOAT plugin load failed: {p_name}")
        except Exception as e:
            raise Exception(f"GOAT plugin initialization failed: {p_name}: {str(e)}")

    tools = []
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_node))
        account: LocalAccount = Account.from_key(private_key)
        w3.eth.default_account = account.address
        w3.middleware_onion.add(SignAndSendRawMiddlewareBuilder.build(account))
        for p_name, plugin in plugins.items():
            p_tools = get_on_chain_tools(
                wallet=Web3EVMWalletClient(w3),
                plugins=[plugin],
            )

            for t in p_tools:
                t.name = f"goat_{p_name}_{t.name.replace(".", "_")}"
                t.description = f"This is {p_name} plugin of GOAT tool, {t.description}"
            tools.extend(p_tools)

    except Exception as e:
        raise Exception(f"GOAT tools initiation failed: {str(e)}")

    return tools
