# Definición de los parámetros del problema (titulos de hojas excel)

# datos: tasa de descuento para valor presente y budget diario para derivaciones y traslados
tasa_descuento = 0.99
budget = 150000

# nombre_hospitales: nombre de los hospitales
dict_hospitales = {
    "Hospital_1": 1,
    "Hospital_2": 2,
    "Hospital_3": 3
}

# nombre_unidades: nombre de las unidades, iternas y externas
dict_unidades = {
    "OR": 1,
    "ICU": 2,
    "SDU/WARD": 3,
    "GA": 4,
    "ED": 5,
    "WL": 6, # agrego WL y PS para mantener la misma nomenclatura en la simulación
    "PS": 7,
    "END": 8 # agrego END para mantener la misma nomenclatura en la simulación, nodo termino
}

# nombres_DRG: nombre de los DRG
dict_drg = {
    "DRG_1": 1,
    "DRG_2": 2,
    "DRG_3": 3,
    "DRG_4": 4,
    "DRG_5": 5,
    "DRG_6": 6,
    "DRG_7": 7,
    "DRG_8": 8
}

# Phi_1, Psi y tau: capacidad de los hospitales y unidades (cantidad camas)
dict_capacidades = {
    dict_hospitales["Hospital_1"]: {
        dict_unidades["OR"]: 6,
        dict_unidades["ICU"]: 60,
        dict_unidades["SDU/WARD"]: 165,
        dict_unidades["GA"]: 15,
        dict_unidades["ED"]: 15
    },
    dict_hospitales["Hospital_2"]: {
        dict_unidades["OR"]: 6,
        dict_unidades["ICU"]: 60,
        dict_unidades["SDU/WARD"]: 165,
        dict_unidades["GA"]: 15,
        dict_unidades["ED"]: 15
    },
    dict_hospitales["Hospital_3"]: {
        dict_unidades["OR"]: 6,
        dict_unidades["ICU"]: 60,
        dict_unidades["SDU/WARD"]: 165,
        dict_unidades["GA"]: 15,
        dict_unidades["ED"]: 15
    }
}

# rho: costo de derivación a PS desde WL (dict_costo_derivar_wl[drg][unidad])
dict_costo_derivar_wl = {
    dict_drg["DRG_1"]: {
        dict_unidades["OR"]: 2105.683943,
        dict_unidades["ICU"]: 1957.261521,
        dict_unidades["SDU/WARD"]: 1162.792468
    },
    dict_drg["DRG_2"]: {
        dict_unidades["OR"]: 2536.390864,
        dict_unidades["ICU"]: 2412.87136,
        dict_unidades["SDU/WARD"]: 1263.905964
    },
    dict_drg["DRG_3"]: {
        dict_unidades["OR"]: 1058.835613,
        dict_unidades["ICU"]: 881.4421404,
        dict_unidades["SDU/WARD"]: 525.1997365
    },
    dict_drg["DRG_4"]: {
        dict_unidades["OR"]: 1954.661669,
        dict_unidades["ICU"]: 1798.860579,
        dict_unidades["SDU/WARD"]: 1115.130125
    },
    dict_drg["DRG_5"]: {
        dict_unidades["OR"]: 958.0795336,
        dict_unidades["ICU"]: 837.5737947,
        dict_unidades["SDU/WARD"]: 515.5510516
    },
    dict_drg["DRG_6"]: {
        dict_unidades["OR"]: 650.8546582,
        dict_unidades["ICU"]: 540.5882262,
        dict_unidades["SDU/WARD"]: 310.7158418
    },
    dict_drg["DRG_7"]: {
        dict_unidades["OR"]: 1561.945032,
        dict_unidades["ICU"]: 1411.735342,
        dict_unidades["SDU/WARD"]: 836.2311842
    },
    dict_drg["DRG_8"]: {
        dict_unidades["OR"]: 1355.643898,
        dict_unidades["ICU"]: 1251.685351,
        dict_unidades["SDU/WARD"]: 758.4039779
    }
}

# theta: costo de derivación a PS desde ED (dict_costo_derivar_ed[hospital][drg][unidad])
dict_costo_derivar_ed = {
    dict_hospitales["Hospital_1"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: 2105.683943,
            dict_unidades["ICU"]: 1957.261521,
            dict_unidades["SDU/WARD"]: 1162.792468
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: 2536.390864,
            dict_unidades["ICU"]: 2412.87136,
            dict_unidades["SDU/WARD"]: 1263.905964
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: 1058.835613,
            dict_unidades["ICU"]: 881.4421404,
            dict_unidades["SDU/WARD"]: 525.1997365
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: 1954.661669,
            dict_unidades["ICU"]: 1798.860579,
            dict_unidades["SDU/WARD"]: 1115.130125
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: 958.0795336,
            dict_unidades["ICU"]: 837.5737947,
            dict_unidades["SDU/WARD"]: 515.5510516
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: 650.8546582,
            dict_unidades["ICU"]: 540.5882262,
            dict_unidades["SDU/WARD"]: 310.7158418
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: 1561.945032,
            dict_unidades["ICU"]: 1411.735342,
            dict_unidades["SDU/WARD"]: 836.2311842
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: 1355.643898,
            dict_unidades["ICU"]: 1251.685351,
            dict_unidades["SDU/WARD"]: 758.4039779
        }
    },
    dict_hospitales["Hospital_2"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: 2105.683943,
            dict_unidades["ICU"]: 1957.261521,
            dict_unidades["SDU/WARD"]: 1162.792468
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: 2536.390864,
            dict_unidades["ICU"]: 2412.87136,
            dict_unidades["SDU/WARD"]: 1263.905964
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: 1058.835613,
            dict_unidades["ICU"]: 881.4421404,
            dict_unidades["SDU/WARD"]: 525.1997365
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: 1954.661669,
            dict_unidades["ICU"]: 1798.860579,
            dict_unidades["SDU/WARD"]: 1115.130125
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: 958.0795336,
            dict_unidades["ICU"]: 837.5737947,
            dict_unidades["SDU/WARD"]: 515.5510516
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: 650.8546582,
            dict_unidades["ICU"]: 540.5882262,
            dict_unidades["SDU/WARD"]: 310.7158418
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: 1561.945032,
            dict_unidades["ICU"]: 1411.735342,
            dict_unidades["SDU/WARD"]: 836.2311842
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: 1355.643898,
            dict_unidades["ICU"]: 1251.685351,
            dict_unidades["SDU/WARD"]: 758.4039779
        }
    },
    dict_hospitales["Hospital_3"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: 2105.683943,
            dict_unidades["ICU"]: 1957.261521,
            dict_unidades["SDU/WARD"]: 1162.792468
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: 2536.390864,
            dict_unidades["ICU"]: 2412.87136,
            dict_unidades["SDU/WARD"]: 1263.905964
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: 1058.835613,
            dict_unidades["ICU"]: 881.4421404,
            dict_unidades["SDU/WARD"]: 525.1997365
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: 1954.661669,
            dict_unidades["ICU"]: 1798.860579,
            dict_unidades["SDU/WARD"]: 1115.130125
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: 958.0795336,
            dict_unidades["ICU"]: 837.5737947,
            dict_unidades["SDU/WARD"]: 515.5510516
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: 650.8546582,
            dict_unidades["ICU"]: 540.5882262,
            dict_unidades["SDU/WARD"]: 310.7158418
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: 1561.945032,
            dict_unidades["ICU"]: 1411.735342,
            dict_unidades["SDU/WARD"]: 836.2311842
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: 1355.643898,
            dict_unidades["ICU"]: 1251.685351,
            dict_unidades["SDU/WARD"]: 758.4039779
        }
    }
}

# vartheta: costo traslado entre hospitales (no importa el hospital en realidad, solo DRG y unidad)
dict_costo_traslado = {
    dict_hospitales["Hospital_1"]: {
        dict_hospitales["Hospital_2"]: {
            dict_drg["DRG_1"]: {
                dict_unidades["OR"]: 71.43574607,
                dict_unidades["ICU"]: 31.90514527,
                dict_unidades["SDU/WARD"]: 18.51741793
            },
            dict_drg["DRG_2"]: {
                dict_unidades["OR"]: 86.04756392,
                dict_unidades["ICU"]: 39.33200057,
                dict_unidades["SDU/WARD"]: 20.12764583
            },
            dict_drg["DRG_3"]: {
                dict_unidades["OR"]: 35.92120851,
                dict_unidades["ICU"]: 14.36830961,
                dict_unidades["SDU/WARD"]: 8.363782262
            },
            dict_drg["DRG_4"]: {
                dict_unidades["OR"]: 66.31228541,
                dict_unidades["ICU"]: 29.32306566,
                dict_unidades["SDU/WARD"]: 17.75839726
            },
            dict_drg["DRG_5"]: {
                dict_unidades["OR"]: 32.5030385,
                dict_unidades["ICU"]: 13.65321563,
                dict_unidades["SDU/WARD"]: 8.210127388
            },
            dict_drg["DRG_6"]: {
                dict_unidades["OR"]: 22.08037357,
                dict_unidades["ICU"]: 8.812080398,
                dict_unidades["SDU/WARD"]: 4.948135854
            },
            dict_drg["DRG_7"]: {
                dict_unidades["OR"]: 52.98929549,
                dict_unidades["ICU"]: 23.01257174,
                dict_unidades["SDU/WARD"]: 13.31694412
            },
            dict_drg["DRG_8"]: {
                dict_unidades["OR"]: 45.99048852,
                dict_unidades["ICU"]: 20.40361112,
                dict_unidades["SDU/WARD"]: 12.07754935
            }
        },
        dict_hospitales["Hospital_3"]: {
            dict_drg["DRG_1"]: {
                dict_unidades["OR"]: 71.43574607,
                dict_unidades["ICU"]: 31.90514527,
                dict_unidades["SDU/WARD"]: 18.51741793
            },
            dict_drg["DRG_2"]: {
                dict_unidades["OR"]: 86.04756392,
                dict_unidades["ICU"]: 39.33200057,
                dict_unidades["SDU/WARD"]: 20.12764583
            },
            dict_drg["DRG_3"]: {
                dict_unidades["OR"]: 35.92120851,
                dict_unidades["ICU"]: 14.36830961,
                dict_unidades["SDU/WARD"]: 8.363782262
            },
            dict_drg["DRG_4"]: {
                dict_unidades["OR"]: 66.31228541,
                dict_unidades["ICU"]: 29.32306566,
                dict_unidades["SDU/WARD"]: 17.75839726
            },
            dict_drg["DRG_5"]: {
                dict_unidades["OR"]: 32.5030385,
                dict_unidades["ICU"]: 13.65321563,
                dict_unidades["SDU/WARD"]: 8.210127388
            },
            dict_drg["DRG_6"]: {
                dict_unidades["OR"]: 22.08037357,
                dict_unidades["ICU"]: 8.812080398,
                dict_unidades["SDU/WARD"]: 4.948135854
            },
            dict_drg["DRG_7"]: {
                dict_unidades["OR"]: 52.98929549,
                dict_unidades["ICU"]: 23.01257174,
                dict_unidades["SDU/WARD"]: 13.31694412
            },
            dict_drg["DRG_8"]: {
                dict_unidades["OR"]: 45.99048852,
                dict_unidades["ICU"]: 20.40361112,
                dict_unidades["SDU/WARD"]: 12.07754935
            }
        }
    },
    dict_hospitales["Hospital_2"]: {
        dict_hospitales["Hospital_1"]: {
            dict_drg["DRG_1"]: {
                dict_unidades["OR"]: 71.43574607,
                dict_unidades["ICU"]: 31.90514527,
                dict_unidades["SDU/WARD"]: 18.51741793
            },
            dict_drg["DRG_2"]: {
                dict_unidades["OR"]: 86.04756392,
                dict_unidades["ICU"]: 39.33200057,
                dict_unidades["SDU/WARD"]: 20.12764583
            },
            dict_drg["DRG_3"]: {
                dict_unidades["OR"]: 35.92120851,
                dict_unidades["ICU"]: 14.36830961,
                dict_unidades["SDU/WARD"]: 8.363782262
            },
            dict_drg["DRG_4"]: {
                dict_unidades["OR"]: 66.31228541,
                dict_unidades["ICU"]: 29.32306566,
                dict_unidades["SDU/WARD"]: 17.75839726
            },
            dict_drg["DRG_5"]: {
                dict_unidades["OR"]: 32.5030385,
                dict_unidades["ICU"]: 13.65321563,
                dict_unidades["SDU/WARD"]: 8.210127388
            },
            dict_drg["DRG_6"]: {
                dict_unidades["OR"]: 22.08037357,
                dict_unidades["ICU"]: 8.812080398,
                dict_unidades["SDU/WARD"]: 4.948135854
            },
            dict_drg["DRG_7"]: {
                dict_unidades["OR"]: 52.98929549,
                dict_unidades["ICU"]: 23.01257174,
                dict_unidades["SDU/WARD"]: 13.31694412
            },
            dict_drg["DRG_8"]: {
                dict_unidades["OR"]: 45.99048852,
                dict_unidades["ICU"]: 20.40361112,
                dict_unidades["SDU/WARD"]: 12.07754935
            }
        },
        dict_hospitales["Hospital_3"]: {
            dict_drg["DRG_1"]: {
                dict_unidades["OR"]: 71.43574607,
                dict_unidades["ICU"]: 31.90514527,
                dict_unidades["SDU/WARD"]: 18.51741793
            },
            dict_drg["DRG_2"]: {
                dict_unidades["OR"]: 86.04756392,
                dict_unidades["ICU"]: 39.33200057,
                dict_unidades["SDU/WARD"]: 20.12764583
            },
            dict_drg["DRG_3"]: {
                dict_unidades["OR"]: 35.92120851,
                dict_unidades["ICU"]: 14.36830961,
                dict_unidades["SDU/WARD"]: 8.363782262
            },
            dict_drg["DRG_4"]: {
                dict_unidades["OR"]: 66.31228541,
                dict_unidades["ICU"]: 29.32306566,
                dict_unidades["SDU/WARD"]: 17.75839726
            },
            dict_drg["DRG_5"]: {
                dict_unidades["OR"]: 32.5030385,
                dict_unidades["ICU"]: 13.65321563,
                dict_unidades["SDU/WARD"]: 8.210127388
            },
            dict_drg["DRG_6"]: {
                dict_unidades["OR"]: 22.08037357,
                dict_unidades["ICU"]: 8.812080398,
                dict_unidades["SDU/WARD"]: 4.948135854
            },
            dict_drg["DRG_7"]: {
                dict_unidades["OR"]: 52.98929549,
                dict_unidades["ICU"]: 23.01257174,
                dict_unidades["SDU/WARD"]: 13.31694412
            },
            dict_drg["DRG_8"]: {
                dict_unidades["OR"]: 45.99048852,
                dict_unidades["ICU"]: 20.40361112,
                dict_unidades["SDU/WARD"]: 12.07754935
            }
        }
    },
    dict_hospitales["Hospital_3"]: {
        dict_hospitales["Hospital_1"]: {
            dict_drg["DRG_1"]: {
                dict_unidades["OR"]: 71.43574607,
                dict_unidades["ICU"]: 31.90514527,
                dict_unidades["SDU/WARD"]: 18.51741793
            },
            dict_drg["DRG_2"]: {
                dict_unidades["OR"]: 86.04756392,
                dict_unidades["ICU"]: 39.33200057,
                dict_unidades["SDU/WARD"]: 20.12764583
            },
            dict_drg["DRG_3"]: {
                dict_unidades["OR"]: 35.92120851,
                dict_unidades["ICU"]: 14.36830961,
                dict_unidades["SDU/WARD"]: 8.363782262
            },
            dict_drg["DRG_4"]: {
                dict_unidades["OR"]: 66.31228541,
                dict_unidades["ICU"]: 29.32306566,
                dict_unidades["SDU/WARD"]: 17.75839726
            },
            dict_drg["DRG_5"]: {
                dict_unidades["OR"]: 32.5030385,
                dict_unidades["ICU"]: 13.65321563,
                dict_unidades["SDU/WARD"]: 8.210127388
            },
            dict_drg["DRG_6"]: {
                dict_unidades["OR"]: 22.08037357,
                dict_unidades["ICU"]: 8.812080398,
                dict_unidades["SDU/WARD"]: 4.948135854
            },
            dict_drg["DRG_7"]: {
                dict_unidades["OR"]: 52.98929549,
                dict_unidades["ICU"]: 23.01257174,
                dict_unidades["SDU/WARD"]: 13.31694412
            },
            dict_drg["DRG_8"]: {
                dict_unidades["OR"]: 45.99048852,
                dict_unidades["ICU"]: 20.40361112,
                dict_unidades["SDU/WARD"]: 12.07754935
            }
        },
        dict_hospitales["Hospital_2"]: {
            dict_drg["DRG_1"]: {
                dict_unidades["OR"]: 71.43574607,
                dict_unidades["ICU"]: 31.90514527,
                dict_unidades["SDU/WARD"]: 18.51741793
            },
            dict_drg["DRG_2"]: {
                dict_unidades["OR"]: 86.04756392,
                dict_unidades["ICU"]: 39.33200057,
                dict_unidades["SDU/WARD"]: 20.12764583
            },
            dict_drg["DRG_3"]: {
                dict_unidades["OR"]: 35.92120851,
                dict_unidades["ICU"]: 14.36830961,
                dict_unidades["SDU/WARD"]: 8.363782262
            },
            dict_drg["DRG_4"]: {
                dict_unidades["OR"]: 66.31228541,
                dict_unidades["ICU"]: 29.32306566,
                dict_unidades["SDU/WARD"]: 17.75839726
            },
            dict_drg["DRG_5"]: {
                dict_unidades["OR"]: 32.5030385,
                dict_unidades["ICU"]: 13.65321563,
                dict_unidades["SDU/WARD"]: 8.210127388
            },
            dict_drg["DRG_6"]: {
                dict_unidades["OR"]: 22.08037357,
                dict_unidades["ICU"]: 8.812080398,
                dict_unidades["SDU/WARD"]: 4.948135854
            },
            dict_drg["DRG_7"]: {
                dict_unidades["OR"]: 52.98929549,
                dict_unidades["ICU"]: 23.01257174,
                dict_unidades["SDU/WARD"]: 13.31694412
            },
            dict_drg["DRG_8"]: {
                dict_unidades["OR"]: 45.99048852,
                dict_unidades["ICU"]: 20.40361112,
                dict_unidades["SDU/WARD"]: 12.07754935
            }
        }
    }
}

# nu: costo social por esperar en lista de espera (1 al 4 nunca estan en wl)
dict_costo_espera_wl = {
    dict_drg["DRG_1"]: {
        dict_unidades["OR"]: 0,
        dict_unidades["ICU"]: 0,
        dict_unidades["SDU/WARD"]: 0
    },
    dict_drg["DRG_2"]: {
        dict_unidades["OR"]: 0,
        dict_unidades["ICU"]: 0,
        dict_unidades["SDU/WARD"]: 0
    },
    dict_drg["DRG_3"]: {
        dict_unidades["OR"]: 0,
        dict_unidades["ICU"]: 0,
        dict_unidades["SDU/WARD"]: 0
    },
    dict_drg["DRG_4"]: {
        dict_unidades["OR"]: 0,
        dict_unidades["ICU"]: 0,
        dict_unidades["SDU/WARD"]: 0
    },
    dict_drg["DRG_5"]: {
        dict_unidades["OR"]: 4.4378762,
        dict_unidades["ICU"]: 4.180640861,
        dict_unidades["SDU/WARD"]: 4.032732341
    },
    dict_drg["DRG_6"]: {
        dict_unidades["OR"]: 6.836340896,
        dict_unidades["ICU"]: 5.810997239,
        dict_unidades["SDU/WARD"]: 5.181694068
    },
    dict_drg["DRG_7"]: {
        dict_unidades["OR"]: 5.337300461,
        dict_unidades["ICU"]: 4.589279284,
        dict_unidades["SDU/WARD"]: 4.301638908
    },
    dict_drg["DRG_8"]: {
        dict_unidades["OR"]: 12.83250264,
        dict_unidades["ICU"]: 10.0173047,
        dict_unidades["SDU/WARD"]: 7.378852624
    }
}

# phi_2: Costo espera de paciente en GA del hospital h (dict_costo_espera_ga[hospital][drg][unidad])
dict_costo_espera_ga = {
    dict_hospitales["Hospital_1"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: 205.8055955,
            dict_unidades["ICU"]: 205.8055955,
            dict_unidades["SDU/WARD"]: 205.8055955
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: 343.0093259,
            dict_unidades["ICU"]: 343.0093259,
            dict_unidades["SDU/WARD"]: 343.0093259
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: 343.0093259,
            dict_unidades["ICU"]: 343.0093259,
            dict_unidades["SDU/WARD"]: 343.0093259
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: 205.8055955,
            dict_unidades["ICU"]: 205.8055955,
            dict_unidades["SDU/WARD"]: 205.8055955
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: 343.0093259,
            dict_unidades["ICU"]: 343.0093259,
            dict_unidades["SDU/WARD"]: 343.0093259
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: 343.0093259,
            dict_unidades["ICU"]: 343.0093259,
            dict_unidades["SDU/WARD"]: 343.0093259
        }
    },
    dict_hospitales["Hospital_2"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: 205.8055955,
            dict_unidades["ICU"]: 205.8055955,
            dict_unidades["SDU/WARD"]: 205.8055955
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: 343.0093259,
            dict_unidades["ICU"]: 343.0093259,
            dict_unidades["SDU/WARD"]: 343.0093259
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: 205.8055955,
            dict_unidades["ICU"]: 205.8055955,
            dict_unidades["SDU/WARD"]: 205.8055955
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: 205.8055955,
            dict_unidades["ICU"]: 205.8055955,
            dict_unidades["SDU/WARD"]: 205.8055955
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: 343.0093259,
            dict_unidades["ICU"]: 343.0093259,
            dict_unidades["SDU/WARD"]: 343.0093259
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: 205.8055955,
            dict_unidades["ICU"]: 205.8055955,
            dict_unidades["SDU/WARD"]: 205.8055955
        }
    },
    dict_hospitales["Hospital_3"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: 343.0093259,
            dict_unidades["ICU"]: 343.0093259,
            dict_unidades["SDU/WARD"]: 343.0093259
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: 205.8055955,
            dict_unidades["ICU"]: 205.8055955,
            dict_unidades["SDU/WARD"]: 205.8055955
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: 343.0093259,
            dict_unidades["ICU"]: 343.0093259,
            dict_unidades["SDU/WARD"]: 343.0093259
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: 205.8055955,
            dict_unidades["ICU"]: 205.8055955,
            dict_unidades["SDU/WARD"]: 205.8055955
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        }
    }
}

# varphi: Costo promedio por periodo de espera de un paciente del ED del hospital h
dict_costo_espera_ed = {
    dict_hospitales["Hospital_1"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: 2074.407461,
            dict_unidades["ICU"]: 1894.407461,
            dict_unidades["SDU/WARD"]: 1294.407461
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: 2857.345768,
            dict_unidades["ICU"]: 2497.345768,
            dict_unidades["SDU/WARD"]: 2317.345768
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: 3965.876614,
            dict_unidades["ICU"]: 3485.876614,
            dict_unidades["SDU/WARD"]: 2705.876614
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: 4657.345768,
            dict_unidades["ICU"]: 3517.345768,
            dict_unidades["SDU/WARD"]: 2857.345768
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: 457.3457678,
            dict_unidades["ICU"]: 457.3457678,
            dict_unidades["SDU/WARD"]: 457.3457678
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: 365.8766142,
            dict_unidades["ICU"]: 365.8766142,
            dict_unidades["SDU/WARD"]: 365.8766142
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: 457.3457678,
            dict_unidades["ICU"]: 457.3457678,
            dict_unidades["SDU/WARD"]: 457.3457678
        }
    },
    dict_hospitales["Hospital_2"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: 2165.876614,
            dict_unidades["ICU"]: 1985.876614,
            dict_unidades["SDU/WARD"]: 1385.876614
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: 2674.407461,
            dict_unidades["ICU"]: 2314.407461,
            dict_unidades["SDU/WARD"]: 2134.407461
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: 4057.345768,
            dict_unidades["ICU"]: 3577.345768,
            dict_unidades["SDU/WARD"]: 2797.345768
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: 4474.407461,
            dict_unidades["ICU"]: 3334.407461,
            dict_unidades["SDU/WARD"]: 2674.407461
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: 365.8766142,
            dict_unidades["ICU"]: 365.8766142,
            dict_unidades["SDU/WARD"]: 365.8766142
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: 457.3457678,
            dict_unidades["ICU"]: 457.3457678,
            dict_unidades["SDU/WARD"]: 457.3457678
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        }
    },
    dict_hospitales["Hospital_3"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: 2257.345768,
            dict_unidades["ICU"]: 2077.345768,
            dict_unidades["SDU/WARD"]: 1477.345768
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: 2765.876614,
            dict_unidades["ICU"]: 2405.876614,
            dict_unidades["SDU/WARD"]: 2225.876614
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: 3874.407461,
            dict_unidades["ICU"]: 3394.407461,
            dict_unidades["SDU/WARD"]: 2614.407461
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: 4565.876614,
            dict_unidades["ICU"]: 3425.876614,
            dict_unidades["SDU/WARD"]: 2765.876614
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: 457.3457678,
            dict_unidades["ICU"]: 457.3457678,
            dict_unidades["SDU/WARD"]: 457.3457678
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: 365.8766142,
            dict_unidades["ICU"]: 365.8766142,
            dict_unidades["SDU/WARD"]: 365.8766142
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: 274.4074607,
            dict_unidades["ICU"]: 274.4074607,
            dict_unidades["SDU/WARD"]: 274.4074607
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: 365.8766142,
            dict_unidades["ICU"]: 365.8766142,
            dict_unidades["SDU/WARD"]: 365.8766142
        }
    }
}

# xi: Costo promedio por periodo de espera de un paciente del hospital h, ubicado en la unidad n1 y necesidad de atención en la unidad n2
dict_costo_espera_hospitalizado = {
    dict_hospitales["Hospital_1"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 383.2993102,
                dict_unidades["SDU/WARD"]: 383.2993102
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 158.4704858,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 140.4704858
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 147.168221,
                dict_unidades["ICU"]: 138.168221,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 638.8321836,
                dict_unidades["SDU/WARD"]: 638.8321836
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 258.1174764,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 234.1174764
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 215.2803683,
                dict_unidades["ICU"]: 197.2803683,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 511.0657469,
                dict_unidades["SDU/WARD"]: 511.0657469
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 223.2939811,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 187.2939811
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 256.2242946,
                dict_unidades["ICU"]: 232.2242946,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 638.8321836,
                dict_unidades["SDU/WARD"]: 638.8321836
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 276.1174764,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 234.1174764
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 305.2803683,
                dict_unidades["ICU"]: 248.2803683,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 383.2993102,
                dict_unidades["SDU/WARD"]: 383.2993102
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 146.4704858,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 140.4704858
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 297.168221,
                dict_unidades["ICU"]: 194.208221,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 638.8321836,
                dict_unidades["SDU/WARD"]: 638.8321836
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 264.1174764,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 234.1174764
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 155.2803683,
                dict_unidades["ICU"]: 134.7603683,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 511.0657469,
                dict_unidades["SDU/WARD"]: 511.0657469
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 202.2939811,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 187.2939811
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 106.2242946,
                dict_unidades["ICU"]: 91.25429464,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 638.8321836,
                dict_unidades["SDU/WARD"]: 638.8321836
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 324.1174764,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 234.1174764
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 275.2803683,
                dict_unidades["ICU"]: 218.9403683,
                dict_unidades["SDU/WARD"]: 0
            }
        }
    },
    dict_hospitales["Hospital_2"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 511.0657469,
                dict_unidades["SDU/WARD"]: 511.0657469
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 205.2939811,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 187.2939811
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 166.2242946,
                dict_unidades["ICU"]: 157.2242946,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 383.2993102,
                dict_unidades["SDU/WARD"]: 383.2993102
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 164.4704858,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 140.4704858
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 177.168221,
                dict_unidades["ICU"]: 159.168221,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 638.8321836,
                dict_unidades["SDU/WARD"]: 638.8321836
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 270.1174764,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 234.1174764
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 275.2803683,
                dict_unidades["ICU"]: 251.2803683,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 383.2993102,
                dict_unidades["SDU/WARD"]: 383.2993102
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 182.4704858,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 140.4704858
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 267.168221,
                dict_unidades["ICU"]: 210.168221,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 511.0657469,
                dict_unidades["SDU/WARD"]: 511.0657469
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 193.2939811,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 187.2939811
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 316.2242946,
                dict_unidades["ICU"]: 213.2642946,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 383.2993102,
                dict_unidades["SDU/WARD"]: 383.2993102
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 170.4704858,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 140.4704858
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 117.168221,
                dict_unidades["ICU"]: 96.64822098,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 638.8321836,
                dict_unidades["SDU/WARD"]: 638.8321836
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 249.1174764,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 234.1174764
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 125.2803683,
                dict_unidades["ICU"]: 110.3103683,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 383.2993102,
                dict_unidades["SDU/WARD"]: 383.2993102
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 230.4704858,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 140.4704858
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 237.168221,
                dict_unidades["ICU"]: 180.828221,
                dict_unidades["SDU/WARD"]: 0
            }
        }
    },
    dict_hospitales["Hospital_3"]: {
        dict_drg["DRG_1"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 638.8321836,
                dict_unidades["SDU/WARD"]: 638.8321836
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 252.1174764,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 234.1174764
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 185.2803683,
                dict_unidades["ICU"]: 176.2803683,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_2"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 511.0657469,
                dict_unidades["SDU/WARD"]: 511.0657469
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 211.2939811,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 187.2939811
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 196.2242946,
                dict_unidades["ICU"]: 178.2242946,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_3"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 383.2993102,
                dict_unidades["SDU/WARD"]: 383.2993102
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 176.4704858,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 140.4704858
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 237.168221,
                dict_unidades["ICU"]: 213.168221,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_4"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 511.0657469,
                dict_unidades["SDU/WARD"]: 511.0657469
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 229.2939811,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 187.2939811
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 286.2242946,
                dict_unidades["ICU"]: 229.2242946,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_5"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 638.8321836,
                dict_unidades["SDU/WARD"]: 638.8321836
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 240.1174764,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 234.1174764
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 335.2803683,
                dict_unidades["ICU"]: 232.3203683,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_6"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 511.0657469,
                dict_unidades["SDU/WARD"]: 511.0657469
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 217.2939811,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 187.2939811
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 136.2242946,
                dict_unidades["ICU"]: 115.7042946,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_7"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 383.2993102,
                dict_unidades["SDU/WARD"]: 383.2993102
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 155.4704858,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 140.4704858
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 87.16822098,
                dict_unidades["ICU"]: 72.19822098,
                dict_unidades["SDU/WARD"]: 0
            }
        },
        dict_drg["DRG_8"]: {
            dict_unidades["OR"]: {
                dict_unidades["OR"]: 0,
                dict_unidades["ICU"]: 511.0657469,
                dict_unidades["SDU/WARD"]: 511.0657469
            },
            dict_unidades["ICU"]: {
                dict_unidades["OR"]: 277.2939811,
                dict_unidades["ICU"]: 0,
                dict_unidades["SDU/WARD"]: 187.2939811
            },
            dict_unidades["SDU/WARD"]: {
                dict_unidades["OR"]: 256.2242946,
                dict_unidades["ICU"]: 199.8842946,
                dict_unidades["SDU/WARD"]: 0
            }
        }
    }
}
