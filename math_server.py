from mcp.server.fastmcp import FastMCP
from typing import List
import math
import statistics

mcp = FastMCP(name="MathServer", stateless_http=True)


@mcp.tool(description="A simple add tool")
def add_two(a: int, b: int) -> int:
    return a + b


@mcp.tool(description="Subtract two numbers: a - b")
def subtract_two(a: int, b: int) -> int:
    return a - b


@mcp.tool(description="Multiply two numbers")
def multiply(a: int, b: int) -> int:
    return a * b


@mcp.tool(description="Divide two numbers: a / b. Raises ValueError on division by zero.")
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b
