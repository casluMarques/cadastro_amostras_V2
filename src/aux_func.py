#função usada para verificar caracteres especiais
import re

def contem_caracteres_invalidos(texto):
    return bool(re.search(r"[\"\'%;#]", texto))