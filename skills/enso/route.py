from typing import Tuple, Type

import httpx
from langchain.tools.base import ToolException
from pydantic import BaseModel, Field

from skills.enso.abi.route import ABI_ROUTE
from utils.random import generate_tx_confirm_string
from utils.tx import EvmContractWrapper, EvmTx

from .base import EnsoBaseTool, base_url, default_chain_id


class EnsoGetRouteShortcutInput(BaseModel):
    chainId: int = Field(
        default_chain_id,
        description="(Optional) Chain ID of the network to execute the transaction on. the default value is the chain_id extracted from networks according to tokenIn and tokenOut",
    )
    amountIn: list[int] = Field(
        description="Amount of tokenIn to swap in wei, you should multiply user's requested value by token decimals."
    )
    tokenIn: list[str] = Field(
        description="Ethereum address of the token to swap or enter into a position from (For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee)."
    )
    tokenOut: list[str] = Field(
        description="Ethereum address of the token to swap or enter into a position to (For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee)."
    )
    # Optional inputs
    # routingStrategy: Literal["router", "delegate", "ensowallet", None] = Field(
    #     None,
    #     description="(Optional) Routing strategy to use. Options: 'ensowallet', 'router', 'delegate'.",
    # )
    # receiver: str | None = Field(
    #     None, description="(Optional) Ethereum address of the receiver of the tokenOut."
    # )
    # spender: str | None = Field(
    #     None, description="(Optional) Ethereum address of the spender of the tokenIn."
    # )
    # amountOut: list[str] | None = Field(
    #     None, description="(Optional) Amount of tokenOut to receive."
    # )
    # minAmountOut: list[str] | None = Field(
    #     None,
    #     description="(Optional) Minimum amount out in wei. If specified, slippage should not be specified.",
    # )
    # slippage: str | None = Field(
    #     None,
    #     description="(Optional) Slippage in basis points (1/10000). If specified, minAmountOut should not be specified.",
    # )
    # fee: list[str] | None = Field(
    #     None,
    #     description="(Optional) Fee in basis points (1/10000) for each amountIn value.",
    # )
    # feeReceiver: str | None = Field(
    #     None,
    #     description="(Optional) Ethereum address that will receive the collected fee if fee was provided.",
    # )
    # disableRFQs: bool | None = Field(
    #     None, description="(Optional) Exclude RFQ sources from routes."
    # )
    # ignoreAggregators: list[str] | None = Field(
    #     None, description="(Optional) List of swap aggregators to ignore."
    # )
    # ignoreStandards: list[str] | None = Field(
    #     None, description="(Optional) List of standards to ignore."
    # )
    # variableEstimates: dict | None = Field(
    #     None, description="Variable estimates for the route."
    # )


class Route(BaseModel):
    tokenIn: list[str] | None = Field(
        None,
        description="Ethereum address of the token to swap or enter into a position from.",
    )
    tokenOut: list[str] | None = Field(
        None,
        description="Ethereum address of the token to swap or enter into a position to.",
    )
    protocol: str | None = Field(None, description="Protocol used for finding route.")
    action: str | None = Field(
        None, description="Action has been done for route (e.g. swap)."
    )
    # internalRoutes: list[str] | None = Field(
    #     None, description="Internal routes needed for the route."
    # )


class EnsoGetRouteShortcutOutput(BaseModel):
    """
    Output content schema for the `/api/v1/shortcuts/route` GET endpoint.
    """

    routeId: str = Field(
        description="The reference code for a found route path, should be shown to the users if the API call gets successful response."
    )
    network: str = Field(
        "The network name of the transaction, according to the input chainId.",
    )
    gas: str | None = Field(
        None,
        description="Estimated gas amount for the transaction.",
    )
    amountOut: str | dict | None = Field(
        None,
        description="The final calculated amountOut as an object. you should multiply the string float value by tokenOut decimals.",
    )
    priceImpact: float | None = Field(
        None,
        description="Price impact in basis points, it is null if USD price is not found.",
    )
    feeAmount: list[str] | None = Field(
        None,
        description="An array of the fee amounts collected for each tokenIn.",
    )
    # createdAt: int | None = Field(
    #     None, description="Block number the transaction was created on."
    # )
    # route: list[Route] | None = Field(
    #     None, description="Route that the shortcut will use."
    # )

    def __str__(self):
        """
        Returns the summary attribute as a string.
        """
        return f"route id: {self.routeId},amount out: {self.amountOut}, price impact: {self.priceImpact}, gas: {self.gas}, fee amount: {self.feeAmount}"


class EnsoGetRouteShortcutArtifact(BaseModel):
    """
    Artifact schema for the `/api/v1/shortcuts/route` GET endpoint.
    """

    routeId: str = Field(
        description="The reference code for a found route path, should be shown to the users if the API call gets successful response."
    )

    def __str__(self):
        """
        Returns the summary attribute as a string.
        """
        return f"route id: {self.routeId}"


class EnsoGetRouteShortcut(EnsoBaseTool):
    """
    This tool finds the optimal execution route path for swap or deposit across a multitude of DeFi protocols such as liquidity pools,
    lending platforms, automated market makers, yield optimizers, and more. This allows for maximized capital efficiency
    and yield optimization, taking into account return rates, gas costs, and slippage.

    IMPORTANT: For each request, the required input parameters should be extracted from user's message, do not fill it
    from your memory, and you should include the network name in the response. the confirmation_code should be shown
    to the users if the API call gets successful response.

    Deposit means to supply the underlying token to its parent token. (e.g. deposit USDC to receive aBasUSDC).

    Attributes:
        name (str): Name of the tool, specifically "enso_get_route_shortcut".
        description (str): Comprehensive description of the tool's purpose and functionality.
        args_schema (Type[BaseModel]): Schema for input arguments, specifying expected parameters.
    """

    description: str = (
        "This tool finds the optimal execution route path for swap or deposit across a multitude of DeFi protocols such as liquidity pools, lending platforms, automated market makers, yield optimizers, and more. This allows for maximized capital efficiency and yield optimization, taking into account return rates, gas costs, and slippage."
    )
    args_schema: Type[BaseModel] = EnsoGetRouteShortcutInput
    response_format: str = "content_and_artifact"

    def _run(
        self,
        amountIn: list[int],
        tokenIn: list[str],
        tokenOut: list[str],
        chainId: int = default_chain_id,
    ) -> Tuple[EnsoGetRouteShortcutOutput, EnsoGetRouteShortcutArtifact]:
        """
        Run the tool to get swap route information.

        Args:
            amountIn (list[int]): Amount of tokenIn to swap in wei, you should multiply user's requested value by token decimals.
            tokenIn (list[str]): Ethereum address of the token to swap or enter into a position from (For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee).
            tokenOut (list[str]): Ethereum address of the token to swap or enter into a position to (For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee).
            chainId (int): The chain id of the network to be used for swap, deposit and routing.

        Returns:
            Tuple[EnsoGetRouteShortcutOutput, EnsoGetRouteShortcutArtifact]: The response containing route shortcut information.
        """
        url = f"{base_url}/api/v1/shortcuts/route"

        headers = {
            "Authorization": f"Bearer {self.api_token}",
        }

        # Prepare query parameters
        params = EnsoGetRouteShortcutInput(
            chainId=chainId,
            amountIn=amountIn,
            tokenIn=tokenIn,
            tokenOut=tokenOut,
        ).model_dump(exclude_none=True)

        params["fromAddress"] = self.wallet.addresses[0].address_id

        with httpx.Client() as client:
            try:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()  # Raise HTTPError for non-2xx responses
                json_dict = response.json()
                # Parse and return the response as a RouteShortcutGetTransaction object
                route_id = generate_tx_confirm_string(10)
                json_dict["routeId"] = route_id

                res = EnsoGetRouteShortcutOutput(**json_dict)

                tx_dict = json_dict.get("tx")
                evm_tx = EvmTx(**tx_dict)
                evm_tx.chainId = chainId

                self.store.save_agent_skill_data(
                    self.agent_id,
                    "enso_route_shortcut",
                    route_id,
                    evm_tx.model_dump(exclude_none=True),
                )

                return (res, EnsoGetRouteShortcutArtifact(routeId=route_id))

            except httpx.RequestError as req_err:
                raise ToolException(
                    f"request error from Enso API: {req_err}"
                ) from req_err
            except httpx.HTTPStatusError as http_err:
                raise ToolException(
                    f"http error from Enso API: {http_err}"
                ) from http_err
            except Exception as e:
                raise ToolException(f"error from Enso API: {e}") from e


class EnsoBroadcastRouteShortcutInput(BaseModel):
    """
    Input model for broadcasting a route transaction.
    """

    routeId: str = Field(
        description="should be filled by you according to your memory from routeId."
    )


class EnsoBroadcastRouteShortcutOutput(BaseModel):
    """
    Output model for broadcasting a transaction.
    """


class EnsoBroadcastRouteShortcutArtifact(BaseModel):
    """
    Artifact model for broadcasting a transaction.
    """

    txHash: str = Field(
        description="The transaction hash of the broadcasted transaction."
    )


class EnsoBroadcastRouteShortcut(EnsoBaseTool):
    """
    This tool is used specifically for broadcasting a route transaction calldata to the network.
    It should only be used when the user explicitly requests to broadcast a route transaction with routeId.

    **Example Usage:**

    "Broadcast the route transaction with routeId: tx-kdv32r342"

    **Important:**
    - This tool should be used with extreme caution.
    - This tool should be run only one time for each routeId.
    - Broadcasting a transaction with a same routeId more than once will result in fund lost.

    Attributes:
        name (str): Name of the tool, specifically "cdp_broadcast_tx".
        description (str): Comprehensive description of the tool's purpose and functionality.
        args_schema (Type[BaseModel]): Schema for input arguments, specifying expected parameters.
    """

    name: str = "enso_broadcast_route_shortcut"
    description: str = (
        "This tool is used specifically for broadcasting a route transaction calldata to the network. It should only be used when the user explicitly requests to broadcast a route transaction with routeId."
    )
    args_schema: Type[BaseModel] = EnsoBroadcastRouteShortcutInput
    response_format: str = "content_and_artifact"

    def _run(
        self, routeId: str
    ) -> Tuple[EnsoBroadcastRouteShortcutOutput, EnsoBroadcastRouteShortcutArtifact]:
        """
        Run the tool to get swap route information.

        Args:
            routeId (str): Transaction reference code generated by EnsoGetRouteShortcut tool and will be passed by user as a confirmation.

        Returns:
            Tuple[EnsoBroadcastRouteShortcutOutput, EnsoBroadcastRouteShortcutArtifact]: The response containing route shortcut information.
        """

        try:
            tx = self.store.get_agent_skill_data(
                self.agent_id, "enso_route_shortcut", routeId
            )

            if not tx:
                raise ToolException(f"transaction not found for routeId: {routeId}")

            if not self.rpc_nodes.get(str(tx.chainId)):
                raise ToolException(f"rpc node not found for chainId: {tx.chainId}")

            contract = EvmContractWrapper(
                self.rpc_nodes[str(tx.chainId)], ABI_ROUTE, tx
            )

            evm_tx = EvmTx(**tx)
            fn, fn_args = contract.decode_function_input(evm_tx.data)

            fn_args["amountIn"] = str(fn_args["amountIn"])

            invocation = self.wallet.invoke_contract(
                contract_address=evm_tx.to,
                method=fn.fn_name,
                abi=ABI_ROUTE,
                args=fn_args,
            ).wait()

            return (
                EnsoBroadcastRouteShortcutOutput(),
                EnsoBroadcastRouteShortcutArtifact(
                    txHash=invocation.transaction.transaction_hash
                ),
            )
        except httpx.RequestError as req_err:
            raise ToolException(f"request error from Enso API: {req_err}") from req_err
        except httpx.HTTPStatusError as http_err:
            raise ToolException(f"http error from Enso API: {http_err}") from http_err
        except Exception as e:
            raise ToolException(f"error from Enso API: {e}") from e
