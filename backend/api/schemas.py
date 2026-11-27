"""Strict request/query schemas for historical research API v1."""
from datetime import date
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,StrictInt,StrictStr,field_validator,model_validator
from backend.artifacts.research_release import RELEASE_ID

Method=Literal['lstm','cnn','persistence']


def iso(value):
    if value is not None and date.fromisoformat(value).isoformat()!=value:raise ValueError('Expected YYYY-MM-DD')
    return value


class PredictionRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',json_schema_extra={'examples':[{
        'release_id':RELEASE_ID,'forecast_origin':'2023-06-15',
        'forecast_length':1,'methods':['lstm','cnn','persistence'],'seed':42}]})
    release_id:StrictStr=RELEASE_ID
    forecast_origin:StrictStr=Field(description='Observed snapshot trading date, YYYY-MM-DD; use /api/v1/forecast-origins for eligible dates.',examples=['2023-06-15'])
    forecast_length:StrictInt=1
    methods:list[Method]=Field(default_factory=lambda:['lstm','persistence'],min_length=1,max_length=3)
    seed:StrictInt=42

    @field_validator('forecast_origin')
    @classmethod
    def origin(cls,value):return iso(value)

    @model_validator(mode='after')
    def contract(self):
        if self.forecast_length not in (1,5):raise ValueError('forecast_length must be 1 or 5')
        if self.seed not in (42,123,456):raise ValueError('seed must be 42, 123 or 456')
        if len(set(self.methods))!=len(self.methods):raise ValueError('methods must be unique')
        if self.forecast_length==5 and 'cnn' in self.methods:raise ValueError('CNN supports one-step only')
        return self


class TraceRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',json_schema_extra={'examples':[{
        'release_id':RELEASE_ID,'forecast_origin':'2023-06-15',
        'forecast_length':5,'seed':42,'detail':'summary'}]})
    release_id:StrictStr=RELEASE_ID
    forecast_origin:StrictStr
    forecast_length:StrictInt=1
    seed:StrictInt=42
    detail:Literal['summary','full']='summary'

    @field_validator('forecast_origin')
    @classmethod
    def origin(cls,value):return iso(value)

    @model_validator(mode='after')
    def contract(self):
        if self.forecast_length not in (1,5) or self.seed not in (42,123,456):raise ValueError('Unsupported mode or seed')
        return self


class PageQuery(BaseModel):
    model_config=ConfigDict(extra='forbid')
    limit:int=Field(100,ge=1,le=1000)
    offset:int=Field(0,ge=0,le=100000)


class RangeQuery(PageQuery):
    release_id:str=RELEASE_ID
    origin_from:str|None=None
    origin_to:str|None=None

    @field_validator('origin_from','origin_to')
    @classmethod
    def dates(cls,value):return iso(value)

    @model_validator(mode='after')
    def order(self):
        if self.origin_from and self.origin_to and self.origin_from>self.origin_to:raise ValueError('origin_from must not exceed origin_to')
        return self


class OriginsQuery(RangeQuery):
    forecast_length:int=1

    @field_validator('forecast_length')
    @classmethod
    def mode(cls,value):
        if value not in (1,5):raise ValueError('forecast_length must be 1 or 5')
        return value


class ResultQuery(OriginsQuery):
    seed:int=42
    methods:list[Method]=Field(default_factory=lambda:['lstm','persistence'])
    split:Literal['val','test']='test'

    @model_validator(mode='after')
    def contract(self):
        if self.seed not in (42,123,456):raise ValueError('Unsupported seed')
        if not self.methods or len(self.methods)>3 or len(set(self.methods))!=len(self.methods):raise ValueError('Expected unique methods')
        if self.forecast_length==5 and 'cnn' in self.methods:raise ValueError('CNN supports one-step only')
        return self


class PriceQuery(BaseModel):
    model_config=ConfigDict(extra='forbid')
    release_id:str=RELEASE_ID
    start_date:str|None=None
    end_date:str|None=None
    limit:int=Field(500,ge=1,le=3000)
    offset:int=Field(0,ge=0,le=100000)

    @field_validator('start_date','end_date')
    @classmethod
    def dates(cls,value):return iso(value)

    @model_validator(mode='after')
    def order(self):
        if self.start_date and self.end_date and self.start_date>self.end_date:raise ValueError('start_date must not exceed end_date')
        return self
