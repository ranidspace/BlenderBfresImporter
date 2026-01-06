import math
from dataclasses import dataclass
from .common import AnimCurve, AnimCurveKeyType, \
    AnimCurveFrameType, AnimCurveType


class CurveAnimHelper:
    target: str
    keyframes: dict[float, object]
    interpolation: AnimCurveType
    frame_type: AnimCurveFrameType
    key_type: AnimCurveKeyType
    wrap_mode: str
    scale: float
    offset: float

    @staticmethod
    def from_curve(curve: AnimCurve, target: str, use_degrees: bool):
        conv_curve = CurveAnimHelper()
        conv_curve.keyframes = {}
        conv_curve.target = target
        conv_curve.scale = curve.scale
        conv_curve.offset = curve.offs
        conv_curve.wrap_mode = f"{curve.pre_wrap}, {curve.post_wrap}"
        conv_curve.interpolation = curve.curve_type
        conv_curve.frame_type = curve.frame_type
        conv_curve.key_type = curve.key_type

        value_scale = curve.scale if curve.scale > 0 else 1
        for i in range(len(curve.frames)):
            frame = curve.frames[i]
            match (curve.curve_type):
                case AnimCurveType.CUBIC:
                    coef0 = curve.keys[i][0] * value_scale + curve.offs
                    slopes = CurveAnimHelper.get_slopes(curve, i)
                    if (use_degrees):
                        coef0 *= 180 / math.pi
                        slopes[0] *= 180 / math.pi
                        slopes[1] *= 180 / math.pi
                    conv_curve.keyframes[frame] = HermiteKey(
                        coef0, slopes[0], slopes[1])
                case AnimCurveType.STEP_BOOL:
                    conv_curve.keyframes[frame] = BooleanKey(
                        curve.key_step_bool_data[i]
                    )
                case AnimCurveType.STEP_INT:
                    conv_curve.keyframes[frame] = KeyFrame(
                        curve.keys[i][0] + curve.offs
                    )
                case AnimCurveType.LINEAR:
                    value = curve.keys[i][0] * value_scale + curve.offs
                    if (use_degrees):
                        value *= 180 / math.pi

                    conv_curve.keyframes[frame] = LinearKeyFrame(
                        value, curve.keys[i][1] * value_scale
                    )
                case _:
                    value = curve.keys[i][0] * value_scale + curve.offs
                    if (use_degrees):
                        value *= 180 / math.pi

                    conv_curve.keyframes[frame] = KeyFrame(
                        value
                    )
        return conv_curve

    @staticmethod
    def get_slopes(curve: AnimCurve, index: float):
        slopes = [0.0, 0.0]
        if (curve.curve_type == AnimCurveType.CUBIC):
            in_slope = 0
            out_slope = 0
            for i in range(len(curve.frames)):
                coef0 = curve.keys[i][0] * curve.scale + curve.offs
                coef1 = curve.keys[i][1] * curve.scale
                coef2 = curve.keys[i][2] * curve.scale
                coef3 = curve.keys[i][3] * curve.scale
                time = 0
                delta = 0
                if (i < len(curve.frames) - 1):
                    next_value = curve.keys[i + 1][0] * \
                        curve.scale + curve.offs
                    delta = next_value - coef0
                    time = curve.frames[i + 1] - curve.frames[i]

                slope_data = CurveAnimHelper.get_cubic_slopes(
                    time, delta,
                    (coef0, coef1, coef2, coef3)
                )

                if (index == i):
                    out_slope = slope_data[i]
                    return [in_slope, out_slope]
                in_slope = slope_data

        return slopes

    @staticmethod
    def get_cubic_slopes(time: float,
                         delta: float,
                         coef: tuple[float, float, float, float]):
        out_slope = coef[1] / time
        param = coef[3] - (-2 * delta)
        in_slope = param / time - out_slope
        return (in_slope, 0 if coef[1] == 0 else out_slope)


@dataclass
class HermiteKey:
    value: float
    in_: float
    out_: float


@dataclass
class BooleanKey:
    value: bool


@dataclass
class LinearKeyFrame:
    value: float
    delta: float


@dataclass
class KeyFrame:
    value: float
