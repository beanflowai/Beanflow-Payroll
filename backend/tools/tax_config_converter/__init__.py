"""
T4127 PDF to JSON Tax Config Converter

Convert CRA T4127 Payroll Deductions Formulas PDF documents
into JSON tax configuration files for the Beanflow-Payroll system.
"""

from .converter import TaxConfigConverter

__all__ = ["TaxConfigConverter"]
