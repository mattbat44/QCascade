from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal

class PathsConfig(BaseModel):
    river_network_shp: str
    discharge_csv: str
    output_name: str
    output_dir: Optional[str] = None

class SedimentConfig(BaseModel):
    range: List[float] = Field(..., min_items=2, max_items=2)
    n_classes: int = Field(..., gt=0)
    deposit_layer_thickness: float = Field(..., ge=0)
    active_layer_depth: Union[float, str]
    active_layer_method: int = 1

class TimeConfig(BaseModel):
    timescale: int = Field(..., gt=0)
    ts_length: float = Field(..., gt=0)

class PhysicsConfig(BaseModel):
    transport_capacity_formula: int = Field(..., ge=1, le=8)
    transport_partitioning: int = Field(..., ge=1, le=4)
    flow_depth_formula: int = 1
    velocity_formula: int = 2
    velocity_partitioning: int = 1
    slope_reduction: int = 1
    width_calculation: int = 1
    update_slope: bool = False
    velocity_height: Union[str, float] = "2D90"
    erosion_max: Optional[float] = None

class OptionsConfig(BaseModel):
    save_deposit_layer: Literal["yearly", "always", "never"] = "never"
    round_parameter: int = 0
    force_pass_external_inputs: bool = False

class DCascadeConfig(BaseModel):
    paths: PathsConfig
    sediment: SedimentConfig
    time: TimeConfig
    physics: PhysicsConfig
    options: OptionsConfig

    def to_json(self, filepath):
        with open(filepath, 'w') as f:
            f.write(self.model_dump_json(indent=4))
