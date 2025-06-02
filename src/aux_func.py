#função usada para verificar caracteres especiais
def contem_caracteres_invalidos(texto):
    return bool(re.search(r"[\"\'%;#]", texto))