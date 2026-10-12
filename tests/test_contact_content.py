import re
from urllib.parse import quote

from consultorio.content import contact_content

from tests import expected_content as expected

PHONE_RE = re.compile(r"^\+?[0-9]{7,}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def test_tc_015_001_el_modulo_define_todos_los_campos_y_coincide_con_el_espejo() -> None:
    assert contact_content.CONTACT_PAGE_TITLE == expected.CONTACT_PAGE_TITLE
    assert contact_content.CONTACT_PAGE_TITLE == "Contacto"
    assert contact_content.ADDRESS_LINES == expected.CONTACT_ADDRESS_LINES
    assert contact_content.PHONE == expected.CONTACT_PHONE
    assert contact_content.WHATSAPP == expected.CONTACT_WHATSAPP
    assert contact_content.EMAIL == expected.CONTACT_EMAIL
    assert contact_content.OFFICE_HOURS == expected.CONTACT_OFFICE_HOURS
    assert contact_content.SOCIAL_LINKS == expected.CONTACT_SOCIAL_LINKS
    assert contact_content.CONTACT_BLOCK_LABELS == expected.CONTACT_BLOCK_LABELS
    assert contact_content.DEFAULT_ADDRESS_LINES == contact_content.ADDRESS_LINES
    assert contact_content.DEFAULT_WHATSAPP == contact_content.WHATSAPP
    assert contact_content.DEFAULT_EMAIL == contact_content.EMAIL
    assert contact_content.DEFAULT_OFFICE_HOURS == contact_content.OFFICE_HOURS
    assert contact_content.DEFAULT_SOCIAL_LINKS == contact_content.SOCIAL_LINKS


def test_tc_015_002_los_formatos_de_contacto_son_validos() -> None:
    assert contact_content.PHONE == "" or PHONE_RE.match(contact_content.PHONE.strip())
    assert PHONE_RE.match(contact_content.WHATSAPP.strip())
    assert EMAIL_RE.match(contact_content.EMAIL.strip())
    assert EMAIL_RE.match("caritogomez26@gmail.com")
    for item in contact_content.SOCIAL_LINKS:
        assert str(item["url"]).strip().startswith("https://"), item
    for item in contact_content.OFFICE_HOURS:
        assert all(str(item[field]).strip() for field in ("label", "days", "hours"))
    assert all(str(line).strip() for line in contact_content.ADDRESS_LINES)


def test_tc_015_003_las_redes_sociales_no_tienen_duplicados_ni_etiquetas_vacias() -> None:
    platforms = [str(item["platform"]).strip() for item in contact_content.SOCIAL_LINKS]
    assert platforms, "al menos la red oficial aprobada (Instagram)"
    assert len(platforms) == len(set(platforms))
    for item in contact_content.SOCIAL_LINKS:
        assert str(item["platform"]).strip()
        assert str(item["label"]).strip()
        assert str(item["url"]).strip()


def test_tc_015_017_los_literales_del_mapa_coinciden_con_el_espejo_y_son_validos() -> None:
    assert contact_content.MAP_QUERY == expected.CONTACT_MAP_QUERY
    assert contact_content.MAP_EMBED_URL == expected.CONTACT_MAP_EMBED_URL
    assert contact_content.MAP_LINK_URL == expected.CONTACT_MAP_LINK_URL
    assert contact_content.MAP_LINK_LABEL == expected.CONTACT_MAP_LINK_LABEL
    assert contact_content.MAP_FRAME_TITLE == expected.CONTACT_MAP_FRAME_TITLE
    assert contact_content.DEFAULT_MAP_QUERY == contact_content.MAP_QUERY

    query = quote(contact_content.MAP_QUERY, safe="")
    assert contact_content.MAP_EMBED_URL == (
        f"https://www.google.com/maps?q={query}&output=embed"
    )
    assert contact_content.MAP_LINK_URL == (
        f"https://www.google.com/maps/search/?api=1&query={query}"
    )
    assert contact_content.MAP_LINK_LABEL == "Abrir en Google Maps"
    assert contact_content.MAP_FRAME_TITLE == "Ubicación del consultorio en Google Maps"
