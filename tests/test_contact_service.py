from consultorio.services import contact_service

from tests import expected_content as expected


def _channel(view: contact_service.ContactView, key: str):
    return next((c for c in view.channels if c.key == key), None)


def test_tc_015_004_get_contact_view_devuelve_los_canale_completos() -> None:
    view = contact_service.get_contact_view()

    assert view.title == expected.CONTACT_PAGE_TITLE
    assert view.fallback_active is False
    keys = [c.key for c in view.channels]
    assert keys == ["address", "whatsapp", "email"]

    address = _channel(view, "address")
    assert address is not None
    assert address.lines == tuple(expected.CONTACT_ADDRESS_LINES)

    whatsapp = _channel(view, "whatsapp")
    assert whatsapp is not None
    assert whatsapp.value == expected.CONTACT_WHATSAPP
    assert whatsapp.href == "https://wa.me/573168756020"

    email = _channel(view, "email")
    assert email is not None
    assert email.value == expected.CONTACT_EMAIL
    assert email.href == f"mailto:{expected.CONTACT_EMAIL}"

    assert _channel(view, "phone") is None

    assert [h.label for h in view.hours] == ["Mañana", "Tarde"]
    for hour, expected_hour in zip(view.hours, expected.CONTACT_OFFICE_HOURS):
        assert hour.days == expected_hour["days"]
        assert hour.hours == expected_hour["hours"]

    assert len(view.socials) == 1
    assert view.socials[0].platform == "instagram"
    assert view.socials[0].label == "Instagram"
    assert view.socials[0].url == expected.CONTACT_SOCIAL_LINKS[0]["url"]

    assert view.titles["address"] == "Dirección"
    assert view.titles["hours"] == "Horarios de atención"
    assert view.titles["social"] == "Redes sociales"


def test_tc_015_005_cl1_direccion_vacia_usa_default_y_sin_default_se_omite(
    monkeypatch,
) -> None:
    monkeypatch.setattr(contact_service, "ADDRESS_LINES", [])

    view = contact_service.get_contact_view()

    assert view.fallback_active is True
    address = _channel(view, "address")
    assert address is not None
    assert address.lines == tuple(expected.CONTACT_ADDRESS_LINES)

    monkeypatch.setattr(contact_service, "ADDRESS_LINES", [])
    monkeypatch.setattr(contact_service, "DEFAULT_ADDRESS_LINES", [])

    view = contact_service.get_contact_view()

    assert _channel(view, "address") is None
    assert _channel(view, "whatsapp") is not None
    assert _channel(view, "email") is not None


def test_tc_015_006_cl2_telefono_ausente_sin_fallback_y_canales_invalidos_en_default(
    monkeypatch,
) -> None:
    base = contact_service.get_contact_view()
    assert _channel(base, "phone") is None
    assert base.fallback_active is False

    monkeypatch.setattr(contact_service, "WHATSAPP", "no-es-un-numero")
    monkeypatch.setattr(contact_service, "EMAIL", "no-es-un-correo")

    view = contact_service.get_contact_view()

    assert view.fallback_active is True
    whatsapp = _channel(view, "whatsapp")
    assert whatsapp is not None
    assert whatsapp.value == expected.CONTACT_WHATSAPP
    email = _channel(view, "email")
    assert email is not None
    assert email.value == expected.CONTACT_EMAIL

    monkeypatch.setattr(contact_service, "WHATSAPP", "no-es-un-numero")
    monkeypatch.setattr(contact_service, "DEFAULT_WHATSAPP", "")
    monkeypatch.setattr(contact_service, "EMAIL", "no-es-un-correo")
    monkeypatch.setattr(contact_service, "DEFAULT_EMAIL", "")

    view = contact_service.get_contact_view()

    assert _channel(view, "whatsapp") is None
    assert _channel(view, "email") is None
    for channel in view.channels:
        if channel.key in ("phone", "whatsapp", "email"):
            assert channel.href


def test_tc_015_007_cl3_horarios_vacios_usan_los_defaults(monkeypatch) -> None:
    monkeypatch.setattr(contact_service, "OFFICE_HOURS", [])

    view = contact_service.get_contact_view()

    assert view.fallback_active is True
    assert [h.label for h in view.hours] == ["Mañana", "Tarde"]
    assert view.hours[0].hours == "8:00 a. m. – 11:30 a. m."

    monkeypatch.setattr(
        contact_service,
        "OFFICE_HOURS",
        [{"label": "", "days": "", "hours": ""}],
    )

    view = contact_service.get_contact_view()

    assert [h.label for h in view.hours] == ["Mañana", "Tarde"]


def test_tc_015_008_cl4_red_invalida_se_omite_y_las_validas_se_conservan(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        contact_service,
        "SOCIAL_LINKS",
        [
            {
                "platform": "instagram",
                "label": "Instagram",
                "url": expected.CONTACT_SOCIAL_LINKS[0]["url"],
            },
            {
                "platform": "facebook",
                "label": "Facebook",
                "url": "http://inseguro.example.com",
            },
            {
                "platform": "tiktok",
                "label": "",
                "url": "https://www.tiktok.com/@ejemplo",
            },
            {
                "platform": "instagram",
                "label": "Instagram duplicada",
                "url": "https://www.instagram.com/otra",
            },
        ],
    )

    view = contact_service.get_contact_view()

    assert view.fallback_active is True
    assert [s.platform for s in view.socials] == ["instagram"]
    assert view.socials[0].label == "Instagram"
    assert view.socials[0].url == expected.CONTACT_SOCIAL_LINKS[0]["url"]


def test_tc_015_018_rf7_mapa_emitido_con_direccion_y_omitido_en_cl1_y_cl5(
    monkeypatch,
) -> None:
    base = contact_service.get_contact_view()
    assert base.map is not None
    assert base.map.embed_url == expected.CONTACT_MAP_EMBED_URL
    assert base.map.link_url == expected.CONTACT_MAP_LINK_URL
    assert base.map.link_label == expected.CONTACT_MAP_LINK_LABEL
    assert base.map.title == expected.CONTACT_MAP_FRAME_TITLE
    assert base.fallback_active is False

    monkeypatch.setattr(contact_service, "MAP_QUERY", "")
    view = contact_service.get_contact_view()
    assert view.map is not None
    assert view.map.embed_url == expected.CONTACT_MAP_EMBED_URL
    assert view.fallback_active is True

    monkeypatch.setattr(contact_service, "DEFAULT_MAP_QUERY", "")
    view = contact_service.get_contact_view()
    assert view.map is None
    assert _channel(view, "address") is not None
    assert view.fallback_active is False

    monkeypatch.undo()

    monkeypatch.setattr(contact_service, "ADDRESS_LINES", [])
    monkeypatch.setattr(contact_service, "DEFAULT_ADDRESS_LINES", [])
    view = contact_service.get_contact_view()
    assert view.map is None
    assert view.fallback_active is True
