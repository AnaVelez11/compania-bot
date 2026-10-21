_QUICK_REPLIES_POR_EMOCION = {
    "Tristeza": ["Quiero contar más", "Prefiero cambiar de tema"],
    "Preocupacion": ["Quiero contarte qué me preocupa", "Ayúdame a distraerme"],
    "Alegria": ["Quiero contarte más", "Compartamos otra cosa"],
    "Neutralidad": ["Sigamos platicando", "Prefiero otra cosa"],
    "Frustracion": ["Quiero contarte más", "Ayúdame a distraerme"],
}


def generar_quick_replies(emocion: str, intencion: str) -> list[str]:
    if intencion == "rechazo_tema":
        return ["Hablemos de algo ligero", "Cuéntame algo bonito"]
    return _QUICK_REPLIES_POR_EMOCION.get(emocion, ["Sigamos platicando", "Otra cosa"])