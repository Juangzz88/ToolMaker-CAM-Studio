"""
ToolMaker CAM Studio - Fuente Única de Verdad para Datos de Materiales e Ingeniería
Centraliza propiedades físicas, energías específicas de corte (u_e) y constantes de rectificado.
"""

# Energías específicas de corte promedio en rectificado / mecanizado [J/mm³ o W·s/mm³]
SPECIFIC_CUTTING_ENERGY = {
    'K': {'name': 'Fundición / Hierro Gris', 'u_e': 38.0, 'kc1_1': 1100.0, 'mc': 0.25},
    'P': {'name': 'Aceros al Carbono / Aleados', 'u_e': 42.0, 'kc1_1': 1500.0, 'mc': 0.25},
    'M': {'name': 'Aceros Inoxidables', 'u_e': 45.0, 'kc1_1': 1800.0, 'mc': 0.23},
    'N': {'name': 'Aluminio / No Ferrosos', 'u_e': 18.0, 'kc1_1': 700.0, 'mc': 0.20},
    'S': {'name': 'Superaleaciones / Titanio', 'u_e': 55.0, 'kc1_1': 2100.0, 'mc': 0.28},
    'H': {'name': 'Materiales Endurecidos (>55 HRC)', 'u_e': 62.0, 'kc1_1': 2500.0, 'mc': 0.30}
}

# Propiedades del Sustrato (Carburo de Tungsteno / Metal Duro)
CARBIDE_PROPERTIES = {
    'E_MODULUS_GPA': 600.0,      # Módulo de Elasticidad (GPa)
    'POISSON_RATIO': 0.22,       # Coeficiente de Poisson
    'DENSITY_G_CM3': 14.5,       # Densidad (g/cm³)
    'K_FACTOR_EULER_DEFAULT': 0.7 # Factor de longitud efectiva para voladizo estándar
}

# Tolerancias Norma ISO 286 para Mangos / Diámetros H6 / H10 (en mm)
ISO_TOLERANCES_MM = {
    '3_or_less':  {'h6': (0.0, -0.006), 'h10': (0.0, -0.040)},
    '3_to_6':     {'h6': (0.0, -0.008), 'h10': (0.0, -0.048)},
    '6_to_10':    {'h6': (0.0, -0.009), 'h10': (0.0, -0.058)},
    '10_to_18':   {'h6': (0.0, -0.011), 'h10': (0.0, -0.070)},
    'above_18':   {'h6': (0.0, -0.013), 'h10': (0.0, -0.084)}
}


def get_material_energy(material_code: str) -> float:
    """Retorna la energía específica de corte u_e según el grupo ISO del material."""
    code = material_code.upper() if material_code else 'P'
    return SPECIFIC_CUTTING_ENERGY.get(code, SPECIFIC_CUTTING_ENERGY['P'])['u_e']