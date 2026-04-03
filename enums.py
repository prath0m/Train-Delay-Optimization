from enum import Enum


class WeatherCondition(Enum):
    CLEAR = "clear"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    FOG = "fog"
    EXTREME_HEAT = "extreme_heat"


class TrainType(Enum):
    SUPERFAST = "superfast"
    EXPRESS = "express"
    MAIL_EXPRESS = "mail_express"
    PASSENGER = "passenger"
    FREIGHT = "freight"
    GOODS = "goods"
