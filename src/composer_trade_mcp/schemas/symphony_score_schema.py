"""
Symphony Score Schema definitions for the composer-mcp-server application.
"""
from typing import Dict, List, Optional, Union, Literal, Tuple, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, ConfigDict, field_validator, GetJsonSchemaHandler, ValidationError
from pydantic.json_schema import JsonSchemaValue
from enum import Enum
import uuid

from ..utils import truncate_text

CRYPTO_ASSETS = ['SOL', 'BCH', 'ETH', 'BTC', 'XRP', 'LTC', 'BAT', 'MKR', 'DOGE', 'XTZ', 'USDC', 'LINK', 'DOT', 'CRV', 'SUSHI', 'UNI', 'YFI', 'AAVE', 'GRT', 'USDT', 'AVAX', 'SHIB']

class Function(str, Enum):
    CUMULATIVE_RETURN = "cumulative-return"
    CURRENT_PRICE = "current-price"
    EXPONENTIAL_MOVING_AVERAGE_PRICE = "exponential-moving-average-price"
    MAX_DRAWDOWN = "max-drawdown"
    MOVING_AVERAGE_PRICE = "moving-average-price"
    MOVING_AVERAGE_RETURN = "moving-average-return"
    RELATIVE_STRENGTH_INDEX = "relative-strength-index"
    STANDARD_DEVIATION_PRICE = "standard-deviation-price"
    STANDARD_DEVIATION_RETURN = "standard-deviation-return"
    ## These functions are not supported yet
    # PERCENTAGE_PRICE_OSCILLATOR = "percentage-price-oscillator"
    # PERCENTAGE_PRICE_OSCILLATOR_SIGNAL = "percentage-price-oscillator-signal"
    # MOVING_AVERAGE_CONVERGENCE_DIVERGENCE = "moving-average-convergence-divergence"
    # MOVING_AVERAGE_CONVERGENCE_DIVERGENCE_SIGNAL = "moving-average-convergence-divergence-signal"
    # LOWER_BOLLINGER = "lower-bollinger"
    # UPPER_BOLLINGER = "upper-bollinger"


class WeightMap(BaseModel):
    num: Annotated[float, Field(gt=0)]
    den: Literal[100]


class UUID(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError('UUID must be a string')
        try:
            uuid_obj = uuid.UUID(v)
            return str(uuid_obj)
        except ValueError:
            raise ValueError('Invalid UUID format')


class WindowParams(TypedDict):
    window: int


class BaseNode(BaseModel):
    model_config = ConfigDict(populate_by_name=False, extra='forbid')
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    )
    weight: Optional[WeightMap]
    
    @field_validator('id')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid_obj = uuid.UUID(v)
            return str(uuid_obj)
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def model_dump(self, **kwargs):
        """Override model_dump to use aliases by default and exclude None values"""
        kwargs.setdefault('by_alias', True)
        kwargs.setdefault('exclude_none', True)
        return super().model_dump(**kwargs)
    
    def model_dump_json(self, **kwargs):
        """Override model_dump_json to use aliases by default and exclude None values"""
        kwargs.setdefault('by_alias', True)
        kwargs.setdefault('exclude_none', True)
        return super().model_dump_json(**kwargs)


class Asset(BaseNode):
    name: Optional[str]
    ticker: str = Field(
        description=f"""
        Asset ticker symbol.
        For stocks, use Xignite format (e.g. BRK/B instead of BRK.B).
        For crypto, use format CRYPTO::SYMBOL//USD (e.g. CRYPTO::BTC//USD).
        Indexes like ^VIX and ^TNX are not supported.
        ### Miscellaneous
        - Please return BIL instead of an empty block when trying to allocate to cash
        - Indexes like ^VIX and ^TNX are not supported
        - bond ETFs like TLT and IEF can be used as a proxy for interest rates, but remember that prices of bond ETFs like TLT and IEF move inversely to interest rates
        - Inverse ETFs can be used as a proxy for short positions
        - Only the following crypto assets are supported:
            - {', '.join(CRYPTO_ASSETS)}
        """
    )
    exchange: Optional[str]
    step: Literal["asset"]


class Empty(BaseNode):
    step: Literal["empty"]


class Filter(BaseNode):
    step: Literal["filter"]
    sort_by_window_days: Optional[int] = Field(alias='sort-by-window-days')
    sort_by_fn_params: Optional[WindowParams] = Field(alias='sort-by-fn-params')
    sort_by_fn: Optional[Function] = Field(alias='sort-by-fn')
    select_n: Optional[int] = Field(alias='select-n')
    select_fn: Optional[Literal["top", "bottom"]] = Field(alias='select-fn')
    children: List[Union["Asset", "Filter", "If", "Group", "WeightCashEqual", 
                        "WeightCashSpecified", "WeightInverseVol", "Empty"]] = Field(default_factory=list)


class WeightInverseVol(BaseNode):
    step: Literal["wt-inverse-vol"]
    window_days: Optional[int] = Field(alias='window-days')
    children: List[Union["Asset", "Filter", "If", "Group", "WeightCashEqual", 
                        "WeightCashSpecified", "WeightInverseVol", "Empty"]] = Field(default_factory=list)


class IfChildTrue(BaseNode):
    step: Literal["if-child"]
    is_else_condition: Literal[False] = Field(False, validation_alias="is-else-condition?", serialization_alias="is-else-condition?")
    children: List[Union["Asset", "Filter", "If", "Group", "WeightCashEqual", 
                        "WeightCashSpecified", "WeightInverseVol", "Empty"]] = Field(default_factory=list)
    comparator: Optional[Literal["gt", "gte", "eq", "lt", "lte"]]
    lhs_fn: Optional[Function] = Field(alias='lhs-fn')
    lhs_val: Optional[str] = Field(alias='lhs-val')
    rhs_val: Optional[float] = Field(alias='rhs-val')
    rhs_fixed_value: Optional[bool] = Field(validation_alias='rhs-fixed-value?', serialization_alias='rhs-fixed-value?')
    rhs_fn: Optional[Function] = Field(alias='rhs-fn')
    lhs_window_days: Optional[int] = Field(alias='lhs-window-days')
    rhs_window_days: Optional[int] = Field(alias='rhs-window-days')
    lhs_fn_params: Optional[WindowParams] = Field(alias='lhs-fn-params')
    rhs_fn_params: Optional[WindowParams] = Field(alias='rhs-fn-params')


class IfChildFalse(BaseNode):
    step: Literal["if-child"]
    is_else_condition: Literal[True] = Field(True, validation_alias="is-else-condition?", serialization_alias="is-else-condition?")
    children: List[Union["Asset", "Filter", "If", "Group", "WeightCashEqual", 
                        "WeightCashSpecified", "WeightInverseVol", "Empty"]] = Field(default_factory=list)


class If(BaseNode):
    step: Literal["if"]
    children: Tuple[IfChildTrue, IfChildFalse]


class Group(BaseNode):
    step: Literal["group"]
    name: Optional[str]
    children: List[Union["WeightCashEqual", "WeightCashSpecified", "WeightInverseVol"]] = Field(default_factory=list)

    @field_validator('children')
    @classmethod
    def validate_single_weight_child(cls, v):
        if len(v) != 1:
            raise ValueError('Group must have exactly one child')
        if not isinstance(v[0], (WeightCashEqual, WeightCashSpecified, WeightInverseVol)):
            raise ValueError('Group child must be a weight node')
        return v


class WeightCashEqual(BaseNode):
    step: Literal["wt-cash-equal"]
    children: List[Union["Asset", "Filter", "If", "Group", "WeightCashEqual", 
                        "WeightCashSpecified", "WeightInverseVol", "Empty"]] = Field(default_factory=list)


class WeightCashSpecified(BaseNode):
    step: Literal["wt-cash-specified"]
    children: List[Union["Asset", "Filter", "If", "Group", "WeightCashEqual", 
                        "WeightCashSpecified", "WeightInverseVol", "Empty"]] = Field(default_factory=list, description="The child weights of a WeightCashSpecified node must sum to 100%")
    # # FIXME: This isn't working.
    # @field_validator('children')
    # @classmethod
    # def validate_children(cls, v):
    #     if sum(child.weight.num for child in v) != 100:
    #         raise ValueError('The child weights of a WeightCashSpecified node must sum to 100%')
    #     return v


class Root(BaseNode):
    step: Literal["root"]
    name: str
    description: str
    rebalance: Literal["none", "daily", "weekly", "monthly", "quarterly", "yearly"]
    rebalance_corridor_width: Optional[float] = Field(alias='rebalance-corridor-width')
    children: List[Union["WeightCashEqual", "WeightCashSpecified", "WeightInverseVol"]] = Field(default_factory=list)

    @field_validator('rebalance_corridor_width')
    @classmethod
    def validate_rebalance_corridor_width(cls, v: Optional[float], info) -> Optional[float]:
        rebalance = info.data.get('rebalance')
        if v is not None and rebalance != "none":
            raise ValueError('rebalance_corridor_width can only be set when rebalance is "none"')
        return v

    @field_validator('rebalance')
    @classmethod
    def validate_rebalance(cls, v: str, info) -> str:
        corridor_width = info.data.get('rebalance_corridor_width')
        if v != "none" and corridor_width is not None:
            raise ValueError('rebalance must be "none" when rebalance_corridor_width is set')
        return v

    @field_validator('children')
    @classmethod
    def validate_single_weight_child(cls, v):
        if len(v) != 1:
            raise ValueError('Root must have exactly one child')
        if not isinstance(v[0], (WeightCashEqual, WeightCashSpecified, WeightInverseVol)):
            raise ValueError('Root child must be a weight node')
        return v


# Update forward references
Filter.model_rebuild()
WeightInverseVol.model_rebuild()
IfChildTrue.model_rebuild()
IfChildFalse.model_rebuild()
Group.model_rebuild()
WeightCashEqual.model_rebuild()
WeightCashSpecified.model_rebuild()
Root.model_rebuild()

# The main schema type
SymphonyScore = Root

def validate_symphony_score(symphony_score: SymphonyScore) -> SymphonyScore:
    """Validate the symphony score."""
    try:
        validated_score = SymphonyScore.model_validate(symphony_score)
        asset_nodes = []
        
        def process_node(node):
            # Ensure all id fields are proper UUIDs
            node.id = str(uuid.uuid4())
            # Collect all asset nodes
            if isinstance(node, Asset):
                asset_nodes.append(node)
            # Process children recursively
            if hasattr(node, 'children'):
                for child in node.children:
                    process_node(child)
        
        # Start processing from the root
        process_node(validated_score)

        if any(node.ticker.startswith('CRYPTO::') for node in asset_nodes):
            if validated_score.rebalance not in ["none", "daily"]:
                raise ValueError('Symphonies with crypto must use daily or threshold (rebalance=None) rebalancing')
        # Check if there are any unsupported crypto assets
        for node in asset_nodes:
            if node.ticker.startswith('CRYPTO::'):
                if node.ticker.split('::')[1].split('//')[0] not in CRYPTO_ASSETS:
                    raise ValueError(f'Unsupported crypto asset: {node.ticker}. Only the following crypto assets are supported: {", ".join(CRYPTO_ASSETS)}')
        return validated_score
    except ValidationError as e:
        raise ValueError(f"Invalid symphony score: {truncate_text(str(e), 1000)}")
