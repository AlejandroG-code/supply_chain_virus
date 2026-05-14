"""
Operaciones Matemáticas Legítimas
=================================

Código real y funcional que genera confianza en el paquete.
El desarrollador lo usará y funcionará perfectamente.
"""

def add(a, b):
    """
    Suma dos números con precisión mejorada.
    
    >>> add(10, 20)
    30.0
    """
    return float(a) + float(b)


def multiply(a, b):
    """
    Multiplica dos números.
    
    >>> multiply(5, 3)
    15.0
    """
    return float(a) * float(b)


def power(base, exponent):
    """
    Calcula potencia.
    
    >>> power(2, 10)
    1024.0
    """
    return float(base) ** float(exponent)


def factorial(n):
    """
    Calcula factorial de n.
    
    >>> factorial(5)
    120
    
    >>> factorial(0)
    1
    """
    if n < 0:
        raise ValueError("Factorial no definido para negativos")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result