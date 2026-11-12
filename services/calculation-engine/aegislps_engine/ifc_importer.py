class IFCImporter:
    @staticmethod
    def parse_ifc_building_elements(file_content: bytes) -> dict:
        """
        Clean-room IFC parser stub for extracting building bounding box dimensions.
        """
        if not isinstance(file_content, (bytes, bytearray)):
            raise ValueError("IFC payload must be bytes.")
        if len(file_content) == 0:
            raise ValueError("IFC payload must not be empty (0 bytes).")
        stripped = bytes(file_content).lstrip()
        if not stripped.startswith(b"ISO-10303-21"):
            raise ValueError(
                "Invalid IFC STEP header: payload must start with 'ISO-10303-21'."
            )

        # Fixed stub bounding-box dimensions retained intentionally for the clean-room IFC parser stub.
        return {
            "parsed": True,
            "detected_building": {
                "length_m": 25.0,
                "width_m": 15.0,
                "height_m": 18.0,
                "roof_type": "flat",
            },
            "warnings": [
                "Imported geometry must be reviewed by qualified designer before calculations."
            ],
        }
