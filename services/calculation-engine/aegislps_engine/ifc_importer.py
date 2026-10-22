class IFCImporter:
    @staticmethod
    def parse_ifc_building_elements(file_content: bytes) -> dict:
        """
        Clean-room IFC parser stub for extracting building bounding box dimensions.
        """
        return {
            "parsed": True,
            "detected_building": {
                "length_m": 25.0,
                "width_m": 15.0,
                "height_m": 18.0,
                "roof_type": "flat"
            },
            "warnings": ["Imported geometry must be reviewed by qualified designer before calculations."]
        }
