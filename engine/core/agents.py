from __future__ import annotations
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Annotated, Literal


class Region(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    neighborhood: list[Region] = Field(default_factory=list)
    
class Person(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    age: int
    parents: list[Person] = Field(default_factory=list)
    children: list[Person] = Field(default_factory=list)
    income: float
    capital: float
    education: int
    nationality: str

class Household(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    members: list[Person] = Field(default_factory=list)
    rent: float
    contracts: list[Contracts] = Field(default_factory=list)
    mortgages: list[Loan] = Field(default_factory=list)
    living_house: House
    houses: list[House] = Field(default_factory=list)
    preference: Region
    income: float
    capital: float
  
  
class House(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    age: int
    evaluation_price: float
    selling_price: float
    total_area: float
    living_area: float
    forSale: bool
    forRent: bool
    owner: Household | Constructor
    quality: float
    typology: Literal['T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6+']
    size: float
    location: Region


class Contracts(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    house: House
    tenant: Household
    landlord: Household | Constructor
    rent: float
    duration: int

class Loan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    house: House
    remaining_morgtage: float
    paid_mortgage: float
    rent: float
    interest_rate: float
    spread: float
    tax_type: Literal['fixed', 'variable']

class Constructor(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    capital: float
    loans: list[Loan] = Field(default_factory=list)
    pending_houses: list[House] = Field(default_factory=list)
    pending_renovations: list[House] = Field(default_factory=list)
    size: float
    



