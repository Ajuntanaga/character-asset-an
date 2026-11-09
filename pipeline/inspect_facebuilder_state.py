from keentools.addon_config import fb_settings

settings = fb_settings()
print({
    "heads": len(settings.heads),
    "current_headnum": settings.current_headnum,
    "items": [
        {
            "head": head.headobj.name if head.headobj else None,
            "cameras": len(head.cameras),
            "pins": [camera.pins_count for camera in head.cameras],
            "texture": head.preview_texture_name(),
        }
        for head in settings.heads
    ],
})
